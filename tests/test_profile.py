"""Tests for the profile page and the password reset flow."""
import re

from django.contrib.auth import get_user_model
from django.core import mail
from django.test import TestCase
from django.urls import reverse

User = get_user_model()

PROFILE_URL = reverse("accounts:profile")
LOGIN_URL = reverse("accounts:login")
PASSWORD_RESET_URL = reverse("accounts:password_reset")
PASSWORD_RESET_DONE_URL = reverse("accounts:password_reset_done")
HOME_URL = reverse("home")

GOOD_PASSWORD = "StrongPass123!"
NEW_PASSWORD = "BrandNewPass456!"


def make_user(**overrides):
    data = {
        "username": "awais",
        "email": "awais@example.com",
        "display_name": "Awais Sabit",
        "password": GOOD_PASSWORD,
    }
    data.update(overrides)
    return User.objects.create_user(**data)


class ProfileTests(TestCase):
    def setUp(self):
        self.user = make_user()

    def test_profile_redirects_anonymous_users_to_login(self):
        response = self.client.get(PROFILE_URL)
        self.assertRedirects(response, f"{LOGIN_URL}?next={PROFILE_URL}")

    def test_signed_in_user_sees_their_details(self):
        self.client.force_login(self.user)
        response = self.client.get(PROFILE_URL)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "accounts/profile.html")
        self.assertContains(response, "awais")
        self.assertContains(response, "awais@example.com")
        self.assertContains(response, "Awais Sabit")
        self.assertContains(response, self.user.date_joined.strftime("%-d %B %Y"))

    def test_updating_the_display_name_saves_it(self):
        self.client.force_login(self.user)
        response = self.client.post(
            PROFILE_URL,
            {"display_name": "Awais the Freelancer", "email": "awais@example.com"},
        )
        self.assertRedirects(response, PROFILE_URL)
        self.user.refresh_from_db()
        self.assertEqual(self.user.display_name, "Awais the Freelancer")
        follow_up = self.client.get(PROFILE_URL)
        self.assertContains(follow_up, "Awais the Freelancer")

    def test_navigation_shows_profile_link_when_signed_in(self):
        self.client.force_login(self.user)
        response = self.client.get(HOME_URL)
        self.assertContains(response, "Profile")
        self.assertContains(response, PROFILE_URL)

    def test_login_page_links_to_password_reset(self):
        response = self.client.get(LOGIN_URL)
        self.assertContains(response, "Forgot your password?")
        self.assertContains(response, PASSWORD_RESET_URL)


class PasswordResetTests(TestCase):
    def setUp(self):
        self.user = make_user()

    def test_password_reset_page_loads(self):
        response = self.client.get(PASSWORD_RESET_URL)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "accounts/password_reset_form.html")

    def test_registered_email_sends_one_email_and_redirects_to_done(self):
        response = self.client.post(
            PASSWORD_RESET_URL, {"email": "awais@example.com"}
        )
        self.assertRedirects(response, PASSWORD_RESET_DONE_URL)
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to, ["awais@example.com"])
        self.assertIn("reset", mail.outbox[0].body.lower())

    def test_unregistered_email_redirects_but_sends_no_email(self):
        response = self.client.post(
            PASSWORD_RESET_URL, {"email": "nobody@example.com"}
        )
        self.assertRedirects(response, PASSWORD_RESET_DONE_URL)
        self.assertEqual(len(mail.outbox), 0)

    def test_full_reset_flow_lets_the_user_log_in_with_the_new_password(self):
        self.client.post(PASSWORD_RESET_URL, {"email": "awais@example.com"})
        self.assertEqual(len(mail.outbox), 1)
        match = re.search(
            r"http://testserver(/accounts/reset/\S+)", mail.outbox[0].body
        )
        self.assertIsNotNone(match, "No reset link found in the email")
        reset_path = match.group(1)

        # Opening the link redirects to the set-password page (Django hides
        # the token from the URL), which shows the new-password form.
        response = self.client.get(reset_path, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "accounts/password_reset_confirm.html")
        set_password_path = response.request["PATH_INFO"]

        response = self.client.post(
            set_password_path,
            {"new_password1": NEW_PASSWORD, "new_password2": NEW_PASSWORD},
        )
        self.assertRedirects(response, reverse("accounts:password_reset_complete"))

        # The old password no longer works; the new one does.
        self.assertFalse(
            self.client.login(username="awais", password=GOOD_PASSWORD)
        )
        self.assertTrue(
            self.client.login(username="awais", password=NEW_PASSWORD)
        )
