"""Link tasks to projects instead of clients.

Tasks now belong to a project (which itself belongs to a client), per
the plan's architecture. There is no production data — only test data —
so the client field is dropped and the project field added outright,
with no data carried across.
"""
import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("projects", "0001_initial"),
        ("tasks", "0002_task_assignee_task_priority"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="task",
            name="client",
        ),
        migrations.AddField(
            model_name="task",
            name="project",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="tasks",
                to="projects.project",
            ),
        ),
    ]
