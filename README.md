# ClientFlow

A Django web app for freelancers and small teams to manage **clients,
projects, tasks and invoices** — without a complicated enterprise CRM.

Built as part of a 30-day portfolio challenge, Nov–Dec 2026, to build three
portfolio projects: ClientFlow (Django), TicketSense (ML) and RepoDoctor
(Python CLI). See `PROGRESS.md` for the build progress.

## Problem

Freelancers juggle clients in spreadsheets, projects in chat threads and
invoices in separate documents. ClientFlow puts the four together in one
simple, tested app with per-user access control, so one user cannot see
another user's clients, projects, tasks or invoices.

## Features that work now

- Registration, login and logout, with a username, email and display name
- Profile page: see your details and update your display name and email
- Password reset by email (reset links print to the console in development)
- Home page and health check
- Responsive Bootstrap 5 interface

## Features planned (MVP)

1. Role-aware access: owner/admin and regular team member
2. Client CRUD with contact details and notes
3. Project CRUD linked to clients
4. Task management with status, priority, due date and assignee
5. Invoice creation with line items, subtotal, tax/discount, total, due date
   and status
6. Dashboard with project/task/invoice summaries
7. Search, filtering, pagination and useful empty states
8. CSV export for invoices or clients
9. Validation, authorization checks and tests throughout
10. Setup guide and sample/demo data command

Out of scope for v1.0.0: payment gateway integration, complex accounting,
multi-currency tax compliance, mobile app, enterprise multi-tenant billing.

## Stack

- Python 3.12, Django 5.1
- PostgreSQL in production (via `DATABASE_URL` or `POSTGRES_*` env vars);
  SQLite by default for local development
- Django templates + Bootstrap 5 (CDN)
- Django's built-in test framework

## Install and run (local development)

```bash
cd clientflow-django
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

cp .env.example .env   # optional; dev works without it
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

Then open http://127.0.0.1:8000/ and http://127.0.0.1:8000/admin/.

## PostgreSQL

Local dev uses SQLite so the app runs with no database server. For
PostgreSQL, either start the bundled compose service or point at your own
server:

```bash
docker compose up -d db
# then in .env:
DATABASE_URL=postgres://clientflow:clientflow-dev-only@localhost:5432/clientflow
python manage.py migrate
```

The compose password is a dev-only placeholder — change it for any shared
or hosted use. Production reads the secret key, allowed hosts and database
from the environment (`config/settings/prod.py` raises an error if
`DJANGO_SECRET_KEY` or `DJANGO_ALLOWED_HOSTS` is missing).

Useful checks:

```bash
python manage.py check
python manage.py test
python manage.py makemigrations --check --dry-run
```

## Project layout

```text
clientflow-django/
├── config/            # project settings (split dev/prod), urls, views
│   └── settings/
│       ├── base.py    # shared settings, DATABASE_URL parsing
│       ├── dev.py
│       └── prod.py
├── apps/
│   ├── accounts/      # custom User model, registration, login and logout
│   ├── clients/       # Client model + CRUD
│   ├── projects/      # Project model + CRUD
│   ├── tasks/         # Task model + CRUD
│   └── billing/       # Invoice models + views
├── templates/         # base.html (Bootstrap 5), home.html, accounts/
├── static/            # css/main.css
├── tests/             # tests for home, health and auth pages
├── .env.example
├── .gitignore
├── docker-compose.yml # PostgreSQL 16 for local use
├── requirements.txt
├── manage.py
└── README.md
```

## Limitations

- Home page, health check and sign-in pages only — no client/project/task/
  invoice features yet.
- Bootstrap is loaded from a CDN, so the pages need internet access for
  full styling; the app itself still renders without it.
- No CI workflow yet.
