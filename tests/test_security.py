"""Security tests for ClientFlow.

These check the real production settings (via `manage.py check
--deploy` in a subprocess, with a proper secret key), the secret-key
rules, and that error pages never leak a stack trace.
"""
import os
import subprocess
import sys

from django.conf import settings
from django.test import TestCase, override_settings
from django.urls import include, path

LONG_KEY = "abcdefghij" * 5  # 50 characters, 10 unique ones


def _run_manage(*args, extra_env=None):
    """Run manage.py in a subprocess and return the finished process."""
    env = dict(os.environ)
    for key in (
        "DJANGO_SECRET_KEY",
        "DJANGO_DEBUG",
        "DJANGO_ALLOWED_HOSTS",
        "DJANGO_SETTINGS_MODULE",
        "DATABASE_URL",
    ):
        env.pop(key, None)
    if extra_env:
        env.update(extra_env)
    return subprocess.run(
        [sys.executable, "manage.py", *args],
        cwd=settings.BASE_DIR,
        env=env,
        capture_output=True,
        text=True,
        timeout=60,
    )


def _boom(request):
    """A view that always fails, so the 500 page can be tested."""
    raise RuntimeError("boom — only here to test the error page")


# The real URLconf is included too, so the error templates can
# still reverse names like 'home' from the base template.
urlpatterns = [path("boom/", _boom), path("", include("config.urls"))]


class DeployCheckTests(TestCase):
    def test_deploy_check_passes_with_production_settings(self):
        result = _run_manage(
            "check",
            "--deploy",
            "--settings=config.settings.prod",
            extra_env={
                "DJANGO_SECRET_KEY": LONG_KEY,
                "DJANGO_ALLOWED_HOSTS": "example.com",
            },
        )
        combined = result.stdout + result.stderr
        self.assertEqual(result.returncode, 0, combined)
        # The only warning left is W021: HSTS preload is deliberately
        # off (joining the preload list is hard to undo). Everything
        # else the deploy check looks for must be clean.
        self.assertIn("security.W021", combined)
        for code in ("W004", "W008", "W009", "W012", "W016", "W018"):
            self.assertNotIn(f"security.{code}", combined)

    def test_production_settings_refuse_a_short_secret_key(self):
        result = _run_manage(
            "check",
            "--settings=config.settings.prod",
            extra_env={
                "DJANGO_SECRET_KEY": "too-short",
                "DJANGO_ALLOWED_HOSTS": "example.com",
            },
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("at least 50 characters", result.stderr)

    def test_production_settings_refuse_a_missing_secret_key(self):
        result = _run_manage(
            "check",
            "--settings=config.settings.prod",
            extra_env={"DJANGO_ALLOWED_HOSTS": "example.com"},
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("DJANGO_SECRET_KEY must be set", result.stderr)

    def test_base_settings_refuse_to_start_without_a_key_when_debug_is_off(
        self,
    ):
        result = _run_manage("check", "--settings=config.settings.base")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("DJANGO_SECRET_KEY must be set", result.stderr)


@override_settings(DEBUG=False, ALLOWED_HOSTS=["testserver"])
class ErrorPageTests(TestCase):
    def test_unknown_page_uses_the_custom_404_page(self):
        response = self.client.get("/no-such-page/")
        self.assertEqual(response.status_code, 404)
        self.assertContains(response, "Page not found", status_code=404)
        self.assertNotContains(response, "Traceback", status_code=404)

    @override_settings(ROOT_URLCONF="tests.test_security")
    def test_server_error_uses_the_custom_500_page_without_a_traceback(self):
        self.client.raise_request_exception = False
        response = self.client.get("/boom/")
        self.assertEqual(response.status_code, 500)
        self.assertContains(response, "Something went wrong", status_code=500)
        self.assertNotContains(response, "Traceback", status_code=500)
        self.assertNotContains(response, "boom — only here", status_code=500)
