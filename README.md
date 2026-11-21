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
- Client records: add, view, edit and delete your own clients, with
  name, email, phone, company and notes — a user can never see, edit or
  delete another user's clients
- Client list search, company filter and pagination: search by name,
  company or email, narrow the list to one of your own companies, 10
  clients per page, with a result count and clear empty states — the
  search and filter never show another user's clients
- Task records: add, view, edit and delete your own tasks, with title,
  description, status (to do, in progress, done), an optional due date
  and a linked project — the list lives under its project, 10 tasks per
  page, and shows the soonest due date first, and a user can never see,
  edit or delete another user's tasks, or attach a task to another
  user's project
- Project records: add, view, edit and delete your own projects, with
  name, description, status (active, on hold, completed), start and due
  dates and a linked client, 10 projects per page — a user can never see,
  edit or delete another user's projects, or attach a project to another
  user's client; each client page lists that client's projects
- Task priority and assignee: every task has a priority (low, medium,
  high — medium by default) and can be assigned to a real user; the
  list shows priority badges and the detail page shows the assignee
- Dashboard at `/dashboard/` for signed-in users: counts of your own
  clients, projects and tasks, tasks by status (to do, in progress,
  done), overdue tasks soonest due first, your newest clients,
  projects and tasks, and quick links to add a client or a project —
  it never shows another user's counts or items
- Invoice records: add, view, edit and delete your own invoices, with
  a client, an optional project, a status (draft, sent, paid,
  overdue), issue and due dates, and line items with quantity and
  unit price — invoice numbers run in sequence per user (INV-0001,
  INV-0002, ...) and the total is worked out from the line items; a
  user can never see, edit or delete another user's invoices
- Invoice status changes: one-click "Mark as sent" and "Mark as paid"
  buttons on the invoice page — draft can move to sent or paid, sent
  and overdue can move to paid, and paid is final; a move that is not
  allowed changes nothing and shows an error; the status can also be
  changed on the edit page
- Invoice list status filter, pagination and CSV export: narrow the
  invoice list to one status, 10 invoices per page with the filter kept
  in the page links, and download your own invoices as a CSV file
  (number, client, project, status, issue date, due date, total) —
  the export covers every invoice, not just the first page, follows
  the same status filter, and another user's invoices never appear
  in it
- Fast list, detail and dashboard pages: related records (clients,
  projects, tasks, assignees and line items) are loaded in a fixed
  number of queries, so a long list costs no more database trips
  than a short one
- Demo data command: `python manage.py seed_demo_data` creates a
  demo user (`demo`, password `DemoPass123!`) with 3 clients,
  4 projects, 8 tasks and 3 invoices, so a new developer can see the
  app populated with one command — running it twice never duplicates
  anything, `--clear` wipes only the demo user's data first, and it
  refuses to run when DEBUG is off unless given `--force`
- Security review: production settings require a secret key of at
  least 50 characters and a non-empty allowed-hosts list, turn on
  secure session and CSRF cookies, force HTTPS with HSTS (one year,
  subdomains included), and refuse to guess content types; friendly
  404 and 500 pages never show a stack trace
- Home page and health check
- Responsive Bootstrap 5 interface

## Features planned (MVP)

1. Role-aware access: owner/admin and regular team member
2. Invoice tax and discount on line items and totals
3. CSV export for clients
4. Validation, authorization checks and tests throughout

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

- Invoices have no tax or discount yet, and only invoices (not
  clients) can be downloaded as a CSV file. Every list is paginated
  at 10 items per page.
- Bootstrap is loaded from a CDN, so the pages need internet access for
  full styling; the app itself still renders without it.
- The demo data command is for local development only: it refuses to
  run when DEBUG is off unless given `--force`, and the demo account
  uses a fixed, published password — never seed demo data on a live
  site.
- No CI workflow yet.
