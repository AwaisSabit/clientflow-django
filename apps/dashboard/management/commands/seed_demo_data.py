"""Seed demo data for ClientFlow.

Creates one demo user ("demo") with a few realistic clients, projects,
tasks and invoices, so a new developer can see the app populated with
a single command:

    python manage.py seed_demo_data

Safety rules, written down here because they matter:

* The command refuses to run when DEBUG is off, unless --force is
  given — demo data must never land in a real deployment by accident.
* Running it twice does not duplicate anything: every record is
  created with get_or_create keyed on the demo user and its natural
  fields (client name, project name, task title, invoice client and
  project).
* --clear wipes the demo user's data first — only that user's data.
  It deletes the demo user itself, and the database cascades the
  delete to their clients, projects, tasks and invoices. Nobody
  else's data is touched.
"""
from datetime import date, timedelta

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError

from apps.billing.models import Invoice, InvoiceLineItem
from apps.clients.models import Client
from apps.projects.models import Project
from apps.tasks.models import Task

DEMO_USERNAME = "demo"
DEMO_EMAIL = "demo@example.com"
DEMO_PASSWORD = "DemoPass123!"

# (name, email, phone, company, notes)
DEMO_CLIENTS = [
    (
        "Sara Ahmed",
        "sara@bakehouse.example",
        "+92 300 1112223",
        "The Bakehouse",
        "Regular customer — a fresh website and an online menu.",
    ),
    (
        "Bilal Khan",
        "bilal@printhouse.example",
        "+92 321 4445556",
        "Print House",
        "Printing shop — business cards, flyers and banners.",
    ),
    (
        "Ayesha Malik",
        "ayesha@events.example",
        "+92 333 7778889",
        "Ayesha Events",
        "Event planner — weddings and corporate events.",
    ),
]

# (client name, project name, status, start days from today, due days
# from today)
DEMO_PROJECTS = [
    ("Sara Ahmed", "Website redesign", Project.Status.ACTIVE, -30, 14),
    ("Sara Ahmed", "Online ordering page", Project.Status.ON_HOLD, -10, 30),
    ("Bilal Khan", "Business card and flyer set", Project.Status.ACTIVE, -7, 10),
    ("Ayesha Malik", "Wedding season campaign", Project.Status.ACTIVE, -5, 45),
]

# (project name, title, status, priority, due days from today)
DEMO_TASKS = [
    ("Website redesign", "Draft the new homepage", Task.Status.DONE, Task.Priority.HIGH, -20),
    ("Website redesign", "Build the menu page", Task.Status.IN_PROGRESS, Task.Priority.MEDIUM, 3),
    ("Website redesign", "Test the contact form", Task.Status.TODO, Task.Priority.LOW, 7),
    ("Online ordering page", "List the payment options", Task.Status.TODO, Task.Priority.MEDIUM, 10),
    ("Business card and flyer set", "Approve the final proof", Task.Status.IN_PROGRESS, Task.Priority.HIGH, -1),
    ("Business card and flyer set", "Send the files to the printer", Task.Status.TODO, Task.Priority.MEDIUM, 5),
    ("Wedding season campaign", "Plan the photo shoot", Task.Status.TODO, Task.Priority.HIGH, 12),
    ("Wedding season campaign", "Write the social media posts", Task.Status.TODO, Task.Priority.MEDIUM, 20),
]

# (client name, project name, status, issue days from today, due days
# from today, [(description, quantity, unit price), ...])
DEMO_INVOICES = [
    (
        "Sara Ahmed",
        "Website redesign",
        Invoice.Status.SENT,
        -10,
        20,
        [("Website design", 1, "850.00"), ("Homepage build", 1, "400.00")],
    ),
    (
        "Bilal Khan",
        "Business card and flyer set",
        Invoice.Status.DRAFT,
        -2,
        14,
        [("Business card design", 1, "120.00"), ("Flyer design", 2, "60.00")],
    ),
    (
        "Ayesha Malik",
        "Wedding season campaign",
        Invoice.Status.PAID,
        -20,
        -5,
        [("Campaign planning", 1, "600.00")],
    ),
]


def _date_from_today(days):
    """A date that many days from today (negative for the past)."""
    return date.today() + timedelta(days=days)


class Command(BaseCommand):
    help = (
        "Create demo data for one demo user: clients, projects, "
        "tasks and invoices. Refuses to run when DEBUG is off unless "
        "--force is given. Safe to run twice — it never duplicates."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--clear",
            action="store_true",
            help="Delete the demo user's data first, then seed it again.",
        )
        parser.add_argument(
            "--force",
            action="store_true",
            help="Allow seeding even when DEBUG is off.",
        )

    def handle(self, *args, **options):
        if not settings.DEBUG and not options["force"]:
            raise CommandError(
                "DEBUG is off, so this command will not seed demo data "
                "here. Run it in development, or pass --force if you "
                "really mean it."
            )

        User = get_user_model()

        if options["clear"]:
            deleted, _ = User.objects.filter(
                username=DEMO_USERNAME
            ).delete()
            if deleted:
                self.stdout.write("Cleared the demo user's data.")
            else:
                self.stdout.write("No demo user to clear.")

        user, user_created = User.objects.get_or_create(
            username=DEMO_USERNAME,
            defaults={"email": DEMO_EMAIL},
        )
        if user_created:
            user.set_password(DEMO_PASSWORD)
            user.save()
            self.stdout.write(
                f"Created demo user {DEMO_USERNAME}."
            )
        else:
            self.stdout.write(
                f"Demo user {DEMO_USERNAME} already exists — "
                "keeping the existing account."
            )

        created_clients = self._seed_clients(user)
        created_projects = self._seed_projects(user)
        created_tasks = self._seed_tasks(user)
        created_invoices, created_items = self._seed_invoices(user)

        self.stdout.write(
            f"Demo data ready: {user.clients.count()} clients "
            f"({created_clients} new), {user.projects.count()} projects "
            f"({created_projects} new), {user.tasks.count()} tasks "
            f"({created_tasks} new), {user.invoices.count()} invoices "
            f"({created_invoices} new, {created_items} new line items)."
        )
        if user_created:
            self.stdout.write(
                f"Log in as {DEMO_USERNAME} with password "
                f"{DEMO_PASSWORD}."
            )

    def _seed_clients(self, user):
        created = 0
        for name, email, phone, company, notes in DEMO_CLIENTS:
            _, was_created = Client.objects.get_or_create(
                owner=user,
                name=name,
                defaults={
                    "email": email,
                    "phone": phone,
                    "company": company,
                    "notes": notes,
                },
            )
            created += was_created
        return created

    def _seed_projects(self, user):
        created = 0
        for client_name, name, status, start_days, due_days in DEMO_PROJECTS:
            client = user.clients.get(name=client_name)
            _, was_created = Project.objects.get_or_create(
                owner=user,
                client=client,
                name=name,
                defaults={
                    "status": status,
                    "start_date": _date_from_today(start_days),
                    "due_date": _date_from_today(due_days),
                },
            )
            created += was_created
        return created

    def _seed_tasks(self, user):
        created = 0
        for project_name, title, status, priority, due_days in DEMO_TASKS:
            project = user.projects.get(name=project_name)
            _, was_created = Task.objects.get_or_create(
                owner=user,
                project=project,
                title=title,
                defaults={
                    "status": status,
                    "priority": priority,
                    "due_date": _date_from_today(due_days),
                },
            )
            created += was_created
        return created

    def _seed_invoices(self, user):
        created_invoices = 0
        created_items = 0
        for (
            client_name,
            project_name,
            status,
            issue_days,
            due_days,
            items,
        ) in DEMO_INVOICES:
            client = user.clients.get(name=client_name)
            project = user.projects.get(name=project_name)
            invoice, was_created = Invoice.objects.get_or_create(
                owner=user,
                client=client,
                project=project,
                defaults={
                    "status": status,
                    "issue_date": _date_from_today(issue_days),
                    "due_date": _date_from_today(due_days),
                },
            )
            created_invoices += was_created
            for description, quantity, unit_price in items:
                _, item_created = InvoiceLineItem.objects.get_or_create(
                    invoice=invoice,
                    description=description,
                    defaults={
                        "quantity": quantity,
                        "unit_price": unit_price,
                    },
                )
                created_items += item_created
        return created_invoices, created_items
