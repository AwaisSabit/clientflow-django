"""Tests for the Client model and its list, create, detail, edit and
delete pages. Every test is written from the owner's point of view:
a signed-in user sees only their own clients, and a client that
belongs to someone else answers with a 404.
"""
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from apps.clients.models import Client

User = get_user_model()

CLIENT_LIST_URL = reverse("clients:list")
CLIENT_CREATE_URL = reverse("clients:create")
LOGIN_URL = reverse("accounts:login")
HOME_URL = reverse("home")

GOOD_PASSWORD = "StrongPass123!"


def make_user(username, **overrides):
    data = {
        "username": username,
        "email": f"{username}@example.com",
        "password": GOOD_PASSWORD,
    }
    data.update(overrides)
    return User.objects.create_user(**data)


def make_client(owner, name="Sara Khan", **overrides):
    data = {
        "name": name,
        "email": "sara@example.com",
        "phone": "0300 1234567",
        "company": "Khan Designs",
        "notes": "Prefers email contact.",
    }
    data.update(overrides)
    return Client.objects.create(owner=owner, **data)


class ClientListTests(TestCase):
    def setUp(self):
        self.user = make_user("awais")
        self.other = make_user("bilal")

    def test_list_redirects_anonymous_users_to_login(self):
        response = self.client.get(CLIENT_LIST_URL)
        self.assertRedirects(response, f"{LOGIN_URL}?next={CLIENT_LIST_URL}")

    def test_empty_list_shows_the_empty_state(self):
        self.client.force_login(self.user)
        response = self.client.get(CLIENT_LIST_URL)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "clients/list.html")
        self.assertContains(response, "No clients yet")

    def test_list_shows_only_the_signed_in_users_clients(self):
        make_client(self.user, name="Sara Khan")
        make_client(self.user, name="Ali Raza", email="ali@example.com")
        make_client(self.other, name="Hidden Client")
        self.client.force_login(self.user)
        response = self.client.get(CLIENT_LIST_URL)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Sara Khan")
        self.assertContains(response, "Ali Raza")
        self.assertNotContains(response, "Hidden Client")

    def test_list_is_ordered_by_name(self):
        make_client(self.user, name="Zara Ahmed")
        make_client(self.user, name="Ahmed Ali")
        self.client.force_login(self.user)
        response = self.client.get(CLIENT_LIST_URL)
        names = [client.name for client in response.context["clients"]]
        self.assertEqual(names, ["Ahmed Ali", "Zara Ahmed"])

    def test_navigation_shows_clients_link_when_signed_in(self):
        self.client.force_login(self.user)
        response = self.client.get(HOME_URL)
        self.assertContains(response, "Clients")
        self.assertContains(response, CLIENT_LIST_URL)


class ClientCreateTests(TestCase):
    def setUp(self):
        self.user = make_user("awais")

    def test_create_page_redirects_anonymous_users_to_login(self):
        response = self.client.get(CLIENT_CREATE_URL)
        self.assertRedirects(response, f"{LOGIN_URL}?next={CLIENT_CREATE_URL}")

    def test_creating_a_client_saves_it_for_the_signed_in_user(self):
        self.client.force_login(self.user)
        response = self.client.post(
            CLIENT_CREATE_URL,
            {
                "name": "Sara Khan",
                "email": "sara@example.com",
                "phone": "0300 1234567",
                "company": "Khan Designs",
                "notes": "Prefers email contact.",
            },
        )
        client = Client.objects.get(name="Sara Khan")
        self.assertRedirects(response, reverse("clients:detail", args=[client.pk]))
        self.assertEqual(client.owner, self.user)
        self.assertEqual(client.email, "sara@example.com")
        self.assertEqual(client.company, "Khan Designs")

    def test_create_needs_a_name(self):
        self.client.force_login(self.user)
        response = self.client.post(CLIENT_CREATE_URL, {"name": ""})
        self.assertEqual(response.status_code, 200)
        self.assertFalse(Client.objects.exists())


class ClientDetailTests(TestCase):
    def setUp(self):
        self.user = make_user("awais")
        self.other = make_user("bilal")
        self.client_obj = make_client(self.user)

    def test_detail_shows_the_clients_details(self):
        self.client.force_login(self.user)
        response = self.client.get(
            reverse("clients:detail", args=[self.client_obj.pk])
        )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "clients/detail.html")
        self.assertContains(response, "Sara Khan")
        self.assertContains(response, "sara@example.com")
        self.assertContains(response, "Khan Designs")
        self.assertContains(response, "Prefers email contact.")

    def test_detail_of_another_users_client_is_a_404(self):
        self.client.force_login(self.other)
        response = self.client.get(
            reverse("clients:detail", args=[self.client_obj.pk])
        )
        self.assertEqual(response.status_code, 404)


class ClientUpdateTests(TestCase):
    def setUp(self):
        self.user = make_user("awais")
        self.other = make_user("bilal")
        self.client_obj = make_client(self.user)

    def test_updating_a_client_saves_the_changes(self):
        self.client.force_login(self.user)
        response = self.client.post(
            reverse("clients:update", args=[self.client_obj.pk]),
            {
                "name": "Sara Khan",
                "email": "sara@newmail.com",
                "phone": "0300 1234567",
                "company": "Khan Designs",
                "notes": "Prefers email contact.",
            },
        )
        self.assertRedirects(
            response, reverse("clients:detail", args=[self.client_obj.pk])
        )
        self.client_obj.refresh_from_db()
        self.assertEqual(self.client_obj.email, "sara@newmail.com")

    def test_updating_another_users_client_is_a_404(self):
        self.client.force_login(self.other)
        response = self.client.post(
            reverse("clients:update", args=[self.client_obj.pk]),
            {"name": "Stolen", "email": "", "phone": "", "company": "", "notes": ""},
        )
        self.assertEqual(response.status_code, 404)
        self.client_obj.refresh_from_db()
        self.assertEqual(self.client_obj.name, "Sara Khan")


class ClientDeleteTests(TestCase):
    def setUp(self):
        self.user = make_user("awais")
        self.other = make_user("bilal")
        self.client_obj = make_client(self.user)

    def test_delete_page_asks_for_confirmation(self):
        self.client.force_login(self.user)
        response = self.client.get(
            reverse("clients:delete", args=[self.client_obj.pk])
        )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "clients/confirm_delete.html")
        self.assertContains(response, "Sara Khan")

    def test_deleting_a_client_removes_it_and_returns_to_the_list(self):
        self.client.force_login(self.user)
        response = self.client.post(
            reverse("clients:delete", args=[self.client_obj.pk])
        )
        self.assertRedirects(response, CLIENT_LIST_URL)
        self.assertFalse(Client.objects.filter(pk=self.client_obj.pk).exists())

    def test_deleting_another_users_client_is_a_404(self):
        self.client.force_login(self.other)
        response = self.client.post(
            reverse("clients:delete", args=[self.client_obj.pk])
        )
        self.assertEqual(response.status_code, 404)
        self.assertTrue(Client.objects.filter(pk=self.client_obj.pk).exists())


class ClientModelTests(TestCase):
    def test_str_returns_the_name(self):
        user = make_user("awais")
        client = make_client(user)
        self.assertEqual(str(client), "Sara Khan")

    def test_client_belongs_to_its_owner(self):
        user = make_user("awais")
        client = make_client(user)
        self.assertEqual(client.owner, user)
        self.assertIn(client, list(user.clients.all()))
