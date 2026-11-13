"""Tests for registration, login and logout."""
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

User = get_user_model()

REGISTER_URL = reverse("accounts:register")
LOGIN_URL = reverse("accounts:login")
LOGOUT_URL = reverse("accounts:logout")
HOME_URL = reverse("home")

GOOD_PASSWORD = "StrongPass123!"


def registration_data(**overrides):
    data = {
        "username": "awais",
        "email": "awais@example.com",
        "display_name": "Awais Sabit",
        "password1": GOOD_PASSWORD,
        "password2": GOOD_PASSWORD,
    }
    data.update(overrides)
    return data


class RegistrationTests(TestCase):
    def test_register_page_loads(self):
        response = self.client.get(REGISTER_URL)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "accounts/register.html")

    def test_registration_creates_user_and_signs_them_in(self):
        response = self.client.post(REGISTER_URL, registration_data())
        self.assertRedirects(response, HOME_URL)
        user = User.objects.get(username="awais")
        self.assertEqual(user.email, "awais@example.com")
        self.assertEqual(user.display_name, "Awais Sabit")
        self.assertTrue(user.check_password(GOOD_PASSWORD))
        self.assertIn("_auth_user_id", self.client.session)
        self.assertEqual(int(self.client.session["_auth_user_id"]), user.pk)

    def test_registration_with_mismatched_passwords_fails(self):
        response = self.client.post(
            REGISTER_URL, registration_data(password2="DifferentPass123!")
        )
        self.assertEqual(response.status_code, 200)
        self.assertFalse(User.objects.filter(username="awais").exists())
        self.assertNotIn("_auth_user_id", self.client.session)


class LoginTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="awais",
            email="awais@example.com",
            display_name="Awais Sabit",
            password=GOOD_PASSWORD,
        )

    def test_login_page_loads(self):
        response = self.client.get(LOGIN_URL)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "accounts/login.html")

    def test_login_works_with_good_details(self):
        response = self.client.post(
            LOGIN_URL, {"username": "awais", "password": GOOD_PASSWORD}
        )
        self.assertRedirects(response, HOME_URL)
        self.assertIn("_auth_user_id", self.client.session)

    def test_login_fails_with_wrong_password(self):
        response = self.client.post(
            LOGIN_URL, {"username": "awais", "password": "WrongPass123!"}
        )
        self.assertEqual(response.status_code, 200)
        self.assertNotIn("_auth_user_id", self.client.session)

    def test_navigation_shows_logout_when_signed_in(self):
        self.client.force_login(self.user)
        response = self.client.get(HOME_URL)
        self.assertContains(response, "Log out")
        self.assertContains(response, "Awais Sabit")
        self.assertNotContains(response, "Create an account")


class LogoutTests(TestCase):
    def test_logout_signs_the_user_out(self):
        User.objects.create_user(username="awais", password=GOOD_PASSWORD)
        self.client.login(username="awais", password=GOOD_PASSWORD)
        self.assertIn("_auth_user_id", self.client.session)
        response = self.client.get(LOGOUT_URL)
        self.assertRedirects(response, HOME_URL)
        self.assertNotIn("_auth_user_id", self.client.session)
        home = self.client.get(HOME_URL)
        self.assertContains(home, "Log in")
