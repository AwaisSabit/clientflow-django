"""Smoke tests for the Day 1 home and health pages."""
from django.test import TestCase
from django.urls import reverse


class HomePageTests(TestCase):
    def test_home_returns_200_and_names_clientflow(self):
        response = self.client.get(reverse("home"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "ClientFlow")
        self.assertTemplateUsed(response, "home.html")

    def test_health_returns_ok_json(self):
        response = self.client.get(reverse("health"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"status": "ok", "app": "clientflow"})
