"""Tests for the Project model and its list, create, detail, edit and
delete pages. Every test is written from the owner's point of view:
a signed-in user sees only their own projects, and a project that
belongs to someone else answers with a 404. The client dropdown only
ever offers the signed-in user's own clients.
"""
from datetime import date

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from apps.clients.models import Client
from apps.projects.models import Project

User = get_user_model()

PROJECT_LIST_URL = reverse("projects:list")
PROJECT_CREATE_URL = reverse("projects:create")
LOGIN_URL = reverse("accounts:login")

GOOD_PASSWORD = "testpass123"


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
        "company": "Khan Designs",
    }
    data.update(overrides)
    return Client.objects.create(owner=owner, **data)


def make_project(owner, client, name="Website redesign", **overrides):
    data = {
        "description": "New site for the client.",
        "status": Project.Status.ACTIVE,
        "start_date": date(2026, 11, 16),
        "due_date": date(2026, 12, 15),
    }
    data.update(overrides)
    return Project.objects.create(owner=owner, client=client, name=name, **data)


def project_form_data(client, **overrides):
    data = {
        "name": "Website redesign",
        "description": "New site for the client.",
        "client": str(client.pk),
        "status": Project.Status.ACTIVE,
        "start_date": "2026-11-16",
        "due_date": "2026-12-15",
    }
    data.update(overrides)
    return data


class ProjectListTests(TestCase):
    def setUp(self):
        self.user = make_user("awais")
        self.other = make_user("bilal")
        self.client_obj = make_client(self.user)

    def test_list_redirects_anonymous_users_to_login(self):
        response = self.client.get(PROJECT_LIST_URL)
        self.assertRedirects(response, f"{LOGIN_URL}?next={PROJECT_LIST_URL}")

    def test_empty_list_shows_the_empty_state(self):
        self.client.force_login(self.user)
        response = self.client.get(PROJECT_LIST_URL)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "No projects yet")

    def test_list_shows_only_the_signed_in_users_projects(self):
        mine = make_project(self.user, self.client_obj, name="Alpha site")
        other_client = make_client(self.other, name="Omar Farooq")
        make_project(
            self.other, other_client, name="Beta shop"
        )
        self.client.force_login(self.user)
        response = self.client.get(PROJECT_LIST_URL)
        self.assertContains(response, mine.name)
        self.assertNotContains(response, "Beta shop")

    def test_list_is_ordered_by_name(self):
        make_project(self.user, self.client_obj, name="Zebra launch")
        make_project(self.user, self.client_obj, name="Alpha site")
        self.client.force_login(self.user)
        response = self.client.get(PROJECT_LIST_URL)
        names = [project.name for project in response.context["projects"]]
        self.assertEqual(names, ["Alpha site", "Zebra launch"])

    def test_nav_shows_projects_link_when_signed_in(self):
        self.client.force_login(self.user)
        response = self.client.get(PROJECT_LIST_URL)
        self.assertContains(response, reverse("projects:list"))
        self.assertContains(response, "Projects")


class ProjectCreateTests(TestCase):
    def setUp(self):
        self.user = make_user("awais")
        self.other = make_user("bilal")
        self.client_obj = make_client(self.user)

    def test_create_redirects_anonymous_users_to_login(self):
        response = self.client.get(PROJECT_CREATE_URL)
        self.assertRedirects(
            response, f"{LOGIN_URL}?next={PROJECT_CREATE_URL}"
        )

    def test_create_saves_a_project_under_the_signed_in_user(self):
        self.client.force_login(self.user)
        response = self.client.post(
            PROJECT_CREATE_URL, project_form_data(self.client_obj)
        )
        project = Project.objects.get(name="Website redesign")
        self.assertEqual(project.owner, self.user)
        self.assertEqual(project.client, self.client_obj)
        self.assertEqual(project.status, Project.Status.ACTIVE)
        self.assertRedirects(
            response, reverse("projects:detail", args=[project.pk])
        )

    def test_create_without_a_name_saves_nothing(self):
        self.client.force_login(self.user)
        response = self.client.post(
            PROJECT_CREATE_URL,
            project_form_data(self.client_obj, name=""),
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Project.objects.count(), 0)

    def test_client_dropdown_only_lists_the_signed_in_users_clients(self):
        make_client(self.other, name="Omar Farooq")
        self.client.force_login(self.user)
        response = self.client.get(PROJECT_CREATE_URL)
        form = response.context["form"]
        client_ids = [c.pk for c in form.fields["client"].queryset]
        self.assertIn(self.client_obj.pk, client_ids)
        self.assertEqual(len(client_ids), 1)

    def test_create_with_another_users_client_is_rejected(self):
        other_client = make_client(self.other, name="Omar Farooq")
        self.client.force_login(self.user)
        response = self.client.post(
            PROJECT_CREATE_URL, project_form_data(other_client)
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Project.objects.count(), 0)


class ProjectDetailTests(TestCase):
    def setUp(self):
        self.user = make_user("awais")
        self.other = make_user("bilal")
        self.client_obj = make_client(self.user)
        self.project = make_project(self.user, self.client_obj)

    def test_detail_shows_the_project(self):
        self.client.force_login(self.user)
        response = self.client.get(
            reverse("projects:detail", args=[self.project.pk])
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.project.name)
        self.assertContains(response, self.client_obj.name)
        self.assertContains(response, "Active")
        self.assertContains(response, "New site for the client.")

    def test_detail_of_another_users_project_answers_404(self):
        self.client.force_login(self.user)
        other_client = make_client(self.other, name="Omar Farooq")
        other_project = make_project(self.other, other_client)
        response = self.client.get(
            reverse("projects:detail", args=[other_project.pk])
        )
        self.assertEqual(response.status_code, 404)

    def test_client_detail_lists_the_clients_projects(self):
        self.client.force_login(self.user)
        response = self.client.get(
            reverse("clients:detail", args=[self.client_obj.pk])
        )
        self.assertContains(response, self.project.name)


class ProjectUpdateTests(TestCase):
    def setUp(self):
        self.user = make_user("awais")
        self.other = make_user("bilal")
        self.client_obj = make_client(self.user)
        self.project = make_project(self.user, self.client_obj)

    def test_update_saves_the_changes(self):
        self.client.force_login(self.user)
        response = self.client.post(
            reverse("projects:update", args=[self.project.pk]),
            project_form_data(
                self.client_obj,
                name="Website relaunch",
                status=Project.Status.ON_HOLD,
            ),
        )
        self.project.refresh_from_db()
        self.assertEqual(self.project.name, "Website relaunch")
        self.assertEqual(self.project.status, Project.Status.ON_HOLD)
        self.assertRedirects(
            response, reverse("projects:detail", args=[self.project.pk])
        )

    def test_update_of_another_users_project_answers_404_and_changes_nothing(self):
        self.client.force_login(self.user)
        other_client = make_client(self.other, name="Omar Farooq")
        other_project = make_project(self.other, other_client)
        response = self.client.post(
            reverse("projects:update", args=[other_project.pk]),
            project_form_data(
                other_client, name="Taken over"
            ),
        )
        self.assertEqual(response.status_code, 404)
        other_project.refresh_from_db()
        self.assertNotEqual(other_project.name, "Taken over")

    def test_update_with_another_users_client_is_rejected(self):
        self.client.force_login(self.user)
        other_client = make_client(self.other, name="Omar Farooq")
        response = self.client.post(
            reverse("projects:update", args=[self.project.pk]),
            project_form_data(other_client),
        )
        self.assertEqual(response.status_code, 200)
        self.project.refresh_from_db()
        self.assertEqual(self.project.client, self.client_obj)


class ProjectDeleteTests(TestCase):
    def setUp(self):
        self.user = make_user("awais")
        self.other = make_user("bilal")
        self.client_obj = make_client(self.user)
        self.project = make_project(self.user, self.client_obj)

    def test_delete_asks_for_confirmation_then_removes_the_project(self):
        self.client.force_login(self.user)
        response = self.client.get(
            reverse("projects:delete", args=[self.project.pk])
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.project.name)
        response = self.client.post(
            reverse("projects:delete", args=[self.project.pk])
        )
        self.assertRedirects(response, PROJECT_LIST_URL)
        self.assertEqual(Project.objects.count(), 0)

    def test_delete_of_another_users_project_answers_404_and_changes_nothing(self):
        self.client.force_login(self.user)
        other_client = make_client(self.other, name="Omar Farooq")
        other_project = make_project(self.other, other_client)
        response = self.client.post(
            reverse("projects:delete", args=[other_project.pk])
        )
        self.assertEqual(response.status_code, 404)
        self.assertEqual(Project.objects.count(), 2)


class ProjectModelTests(TestCase):
    def test_str_returns_the_name(self):
        user = make_user("awais")
        client = make_client(user)
        project = make_project(user, client, name="Website redesign")
        self.assertEqual(str(project), "Website redesign")

    def test_owner_and_client_can_reach_the_project(self):
        user = make_user("awais")
        client = make_client(user)
        project = make_project(user, client)
        self.assertIn(project, list(user.projects.all()))
        self.assertIn(project, list(client.projects.all()))
