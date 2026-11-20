"""Tests for the seed_demo_data management command."""
from io import StringIO

from django.contrib.auth import get_user_model
from django.core.management import CommandError, call_command
from django.test import TestCase, override_settings

from apps.billing.models import Invoice, InvoiceLineItem
from apps.clients.models import Client
from apps.projects.models import Project
from apps.tasks.models import Task
from apps.dashboard.management.commands.seed_demo_data import (
    DEMO_EMAIL,
    DEMO_PASSWORD,
    DEMO_USERNAME,
)


def _seed(stdout=None):
    """Run the seed command and return its printed output."""
    out = stdout or StringIO()
    call_command("seed_demo_data", stdout=out)
    return out.getvalue()


# The test runner forces DEBUG off, so tests that expect the command
# to seed must switch it back on; the refusal tests below override it
# to False again on their own methods.
@override_settings(DEBUG=True)
class SeedDemoDataTests(TestCase):
    def test_creates_demo_user_clients_projects_tasks_and_invoices(self):
        output = _seed()

        user = get_user_model().objects.get(username=DEMO_USERNAME)
        self.assertEqual(user.email, DEMO_EMAIL)
        self.assertTrue(user.check_password(DEMO_PASSWORD))
        self.assertEqual(Client.objects.filter(owner=user).count(), 3)
        self.assertEqual(Project.objects.filter(owner=user).count(), 4)
        self.assertEqual(Task.objects.filter(owner=user).count(), 8)
        self.assertEqual(Invoice.objects.filter(owner=user).count(), 3)
        self.assertEqual(
            InvoiceLineItem.objects.filter(invoice__owner=user).count(), 5
        )
        # The seeded data hangs together: a project belongs to its
        # client, a task to its project, an invoice to its client.
        project = Project.objects.get(
            owner=user, name="Website redesign"
        )
        self.assertEqual(project.client.name, "Sara Ahmed")
        self.assertEqual(
            Task.objects.filter(project=project).count(), 3
        )
        invoice = Invoice.objects.get(owner=user, project=project)
        self.assertEqual(invoice.client.name, "Sara Ahmed")
        self.assertEqual(invoice.status, Invoice.Status.SENT)
        # The summary says what was created.
        self.assertIn("3 clients (3 new)", output)
        self.assertIn("4 projects (4 new)", output)
        self.assertIn("8 tasks (8 new)", output)
        self.assertIn("3 invoices (3 new", output)

    def test_demo_user_can_sign_in(self):
        _seed()
        self.assertTrue(
            self.client.login(
                username=DEMO_USERNAME, password=DEMO_PASSWORD
            )
        )
        response = self.client.get("/dashboard/")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Sara Ahmed")

    def test_running_twice_does_not_duplicate(self):
        first_output = _seed()
        second_output = _seed()

        user = get_user_model().objects.get(username=DEMO_USERNAME)
        self.assertEqual(Client.objects.filter(owner=user).count(), 3)
        self.assertEqual(Project.objects.filter(owner=user).count(), 4)
        self.assertEqual(Task.objects.filter(owner=user).count(), 8)
        self.assertEqual(Invoice.objects.filter(owner=user).count(), 3)
        self.assertEqual(
            InvoiceLineItem.objects.filter(invoice__owner=user).count(), 5
        )
        self.assertIn("already exists", second_output)
        self.assertIn("3 clients (0 new)", second_output)
        self.assertIn("4 projects (0 new)", second_output)
        self.assertIn("8 tasks (0 new)", second_output)
        self.assertIn("3 invoices (0 new", second_output)
        self.assertIn("3 clients (3 new)", first_output)

    def test_clear_removes_only_the_demo_users_data(self):
        other = get_user_model().objects.create_user(
            username="other", password="other-pass-123"
        )
        Client.objects.create(owner=other, name="Other Client")
        _seed()
        demo = get_user_model().objects.get(username=DEMO_USERNAME)
        # An extra record the demo user made outside the seed data.
        Client.objects.create(owner=demo, name="Extra Client")

        out = StringIO()
        call_command("seed_demo_data", "--clear", stdout=out)
        output = out.getvalue()

        self.assertIn("Cleared the demo user's data.", output)
        # The extra record is gone, and the seed ran again after
        # clearing, so the demo data is back fresh — exactly once.
        self.assertFalse(
            Client.objects.filter(name="Extra Client").exists()
        )
        user = get_user_model().objects.get(username=DEMO_USERNAME)
        self.assertEqual(Client.objects.filter(owner=user).count(), 3)
        self.assertEqual(Invoice.objects.filter(owner=user).count(), 3)
        # The other user's data was never touched.
        self.assertTrue(
            get_user_model().objects.filter(username="other").exists()
        )
        self.assertEqual(
            Client.objects.filter(owner=other).count(), 1
        )

    def test_clear_with_no_demo_user_says_so(self):
        out = StringIO()
        call_command("seed_demo_data", "--clear", stdout=out)
        self.assertIn("No demo user to clear.", out.getvalue())
        self.assertTrue(
            get_user_model().objects.filter(
                username=DEMO_USERNAME
            ).exists()
        )

    @override_settings(DEBUG=False)
    def test_refuses_when_debug_is_off_without_force(self):
        with self.assertRaisesMessage(
            CommandError, "DEBUG is off"
        ):
            call_command("seed_demo_data", stdout=StringIO())
        self.assertFalse(
            get_user_model().objects.filter(
                username=DEMO_USERNAME
            ).exists()
        )

    @override_settings(DEBUG=False)
    def test_force_allows_seeding_when_debug_is_off(self):
        out = StringIO()
        call_command("seed_demo_data", "--force", stdout=out)
        self.assertTrue(
            get_user_model().objects.filter(
                username=DEMO_USERNAME
            ).exists()
        )
        self.assertIn("3 clients (3 new)", out.getvalue())
