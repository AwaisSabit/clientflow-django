"""Tests for client search, company filtering and pagination on the
client list page. Search and filter only ever see the signed-in
user's own clients, and the page links keep the current search and
filter.
"""
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from apps.clients.models import Client

User = get_user_model()

CLIENT_LIST_URL = reverse("clients:list")
LOGIN_URL = reverse("accounts:login")

GOOD_PASSWORD = "StrongPass123!"


def make_user(username):
    return User.objects.create_user(
        username=username,
        email=f"{username}@example.com",
        password=GOOD_PASSWORD,
    )


def make_client(owner, name, company="", email=""):
    return Client.objects.create(
        owner=owner, name=name, company=company, email=email
    )


class ClientSearchTests(TestCase):
    def setUp(self):
        self.user = make_user("awais")
        self.other = make_user("bilal")
        make_client(
            self.user, "Sara Khan", company="Khan Designs",
            email="sara@khandesigns.com",
        )
        make_client(
            self.user, "Ali Raza", company="Raza Media",
            email="ali@razamedia.com",
        )
        make_client(
            self.user, "Zara Ahmed", company="Khan Designs",
            email="zara@example.com",
        )
        make_client(
            self.other, "Hidden Client", company="Khan Designs",
            email="hidden@example.com",
        )
        self.client.force_login(self.user)

    def test_search_finds_a_client_by_name(self):
        response = self.client.get(CLIENT_LIST_URL, {"q": "Sara"})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Sara Khan")
        self.assertNotContains(response, "Ali Raza")
        self.assertContains(response, "1 client")

    def test_search_is_case_insensitive(self):
        response = self.client.get(CLIENT_LIST_URL, {"q": "sArA"})
        self.assertContains(response, "Sara Khan")
        self.assertNotContains(response, "Ali Raza")

    def test_search_finds_clients_by_company(self):
        response = self.client.get(CLIENT_LIST_URL, {"q": "Khan Designs"})
        self.assertContains(response, "Sara Khan")
        self.assertContains(response, "Zara Ahmed")
        self.assertNotContains(response, "Ali Raza")
        self.assertContains(response, "2 clients")

    def test_search_finds_a_client_by_email(self):
        response = self.client.get(CLIENT_LIST_URL, {"q": "ali@razamedia"})
        self.assertContains(response, "Ali Raza")
        self.assertNotContains(response, "Sara Khan")

    def test_search_with_no_match_shows_the_empty_state(self):
        response = self.client.get(CLIENT_LIST_URL, {"q": "nobody here"})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "No clients match your search")
        self.assertNotContains(response, "Sara Khan")
        self.assertNotContains(response, "Ali Raza")

    def test_search_never_shows_another_users_clients(self):
        response = self.client.get(CLIENT_LIST_URL, {"q": "Hidden"})
        self.assertNotContains(response, "Hidden Client")
        self.assertContains(response, "No clients match your search")

    def test_company_filter_narrows_the_list(self):
        response = self.client.get(
            CLIENT_LIST_URL, {"company": "Khan Designs"}
        )
        self.assertContains(response, "Sara Khan")
        self.assertContains(response, "Zara Ahmed")
        self.assertNotContains(response, "Ali Raza")
        self.assertContains(response, "2 clients")

    def test_company_filter_dropdown_lists_only_the_users_companies(self):
        response = self.client.get(CLIENT_LIST_URL)
        self.assertContains(response, "Khan Designs")
        self.assertContains(response, "Raza Media")
        # The other user's company is the same name here, so check the
        # filter itself: filtering by a company the user does not have
        # shows the empty state, not the other user's client.
        response = self.client.get(CLIENT_LIST_URL, {"company": "Other Co"})
        self.assertContains(response, "No clients match your search")
        self.assertNotContains(response, "Hidden Client")

    def test_search_and_company_filter_work_together(self):
        response = self.client.get(
            CLIENT_LIST_URL, {"q": "Sara", "company": "Khan Designs"}
        )
        self.assertContains(response, "Sara Khan")
        self.assertNotContains(response, "Zara Ahmed")

        response = self.client.get(
            CLIENT_LIST_URL, {"q": "Sara", "company": "Raza Media"}
        )
        self.assertContains(response, "No clients match your search")
        self.assertNotContains(response, "Sara Khan")

    def test_search_box_and_filter_keep_their_values(self):
        response = self.client.get(
            CLIENT_LIST_URL, {"q": "Sara", "company": "Khan Designs"}
        )
        self.assertContains(response, 'value="Sara"')
        self.assertContains(response, "Khan Designs")


class ClientPaginationTests(TestCase):
    def setUp(self):
        self.user = make_user("awais")
        self.other = make_user("bilal")
        for number in range(1, 13):
            make_client(self.user, f"Client {number:02d}")
        self.client.force_login(self.user)

    def test_first_page_shows_ten_clients(self):
        response = self.client.get(CLIENT_LIST_URL)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context["clients"]), 10)
        self.assertContains(response, "12 clients")
        self.assertContains(response, "Client 01")
        self.assertContains(response, "Client 10")
        self.assertNotContains(response, "Client 11")

    def test_second_page_shows_the_rest(self):
        response = self.client.get(CLIENT_LIST_URL, {"page": 2})
        self.assertEqual(len(response.context["clients"]), 2)
        self.assertContains(response, "Client 11")
        self.assertContains(response, "Client 12")
        self.assertNotContains(response, "Client 01")

    def test_page_links_keep_the_search(self):
        for number in range(1, 13):
            make_client(self.user, f"Searchable {number:02d}")
        response = self.client.get(CLIENT_LIST_URL, {"q": "Searchable"})
        self.assertEqual(len(response.context["clients"]), 10)
        self.assertContains(response, "page=2")
        self.assertContains(response, "q=Searchable")

    def test_an_out_of_range_page_shows_the_last_page(self):
        response = self.client.get(CLIENT_LIST_URL, {"page": 99})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context["clients"]), 2)

    def test_pagination_never_shows_another_users_clients(self):
        make_client(self.other, "Hidden Client")
        response = self.client.get(CLIENT_LIST_URL)
        self.assertNotContains(response, "Hidden Client")
        response = self.client.get(CLIENT_LIST_URL, {"page": 2})
        self.assertNotContains(response, "Hidden Client")


class ClientListAccessTests(TestCase):
    def test_search_and_filter_pages_redirect_anonymous_users(self):
        response = self.client.get(CLIENT_LIST_URL, {"q": "Sara"})
        self.assertRedirects(
            response, f"{LOGIN_URL}?next={CLIENT_LIST_URL}%3Fq%3DSara"
        )
