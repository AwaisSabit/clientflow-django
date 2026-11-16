# ClientFlow — Progress Log

## Day 1 — 2026-11-12 (Project A, ClientFlow)

### Done
- Created the repo structure from the plan: `config/`, `apps/accounts`,
  `apps/clients`, `apps/projects`, `apps/tasks`, `apps/billing`,
  `templates/`, `static/`, `tests/`.
- Working Django 5.1 project: split settings (`config/settings/base.py`,
  `dev.py`, `prod.py`) with env vars only; `.env.example` with no real
  secrets; PostgreSQL via `DATABASE_URL` / `POSTGRES_*`, defaulting to
  local SQLite for dev; `docker-compose.yml` for PostgreSQL 16.
- Custom user model `accounts.User` (with a `display_name` field) defined
  before the first migration, plus admin registration.
- `apps/clients` started as a skeleton package; its model and CRUD are
  scheduled for Day 5–6. `projects`, `tasks`, `billing` are empty
  packages with `apps.py` for now.
- Base template with Bootstrap 5 layout, home page (`/`) and health
  endpoint (`/health/` → `{"status": "ok", "app": "clientflow"}`).
- Smoke tests in `tests/test_home.py` for the home page (200, contains
  "ClientFlow", uses `home.html`) and the health endpoint.
- `requirements.txt` (Django 5.1, psycopg 3), `.gitignore`
  (Python/Django, `.env`, `.venv`, `__pycache__`, `db.sqlite3`),
  `README.md` with install/run and PostgreSQL notes.
- Local git repo initialised; **nothing pushed — GitHub is not connected
  yet** (no remote), so commits are local only until the user connects
  GitHub and selects the `clientflow-django` repository.

### Test results (Day 1)
- `python manage.py check` — passed, no issues.
- `python manage.py test` — 2 tests, all passed.
- `python manage.py makemigrations --check --dry-run` — no changes detected.
- `git diff --check` — clean; no secrets found in the diff.

### Commits (local only)
- See `git log` in the project repo (2 real commits, in plain English).

### Next steps — Day 2 (auth setup)
Per the plan: configure apps, base template (done Day 1), Bootstrap
layout (done Day 1), health/home page (done Day 1); Day 2 in the plan
is the same scope, so Day 2 moves to the Day 3 work: authentication —
registration, login, logout — using the custom user model, plus auth
tests. Also: connect GitHub (user action) so Day 2 work can be pushed
to the `clientflow-django` repository.

## Day 2 — 2026-11-13 (ClientFlow)

### Done
- Registration, login and logout, built on Django's built-in auth and
  the existing custom `accounts.User` model (no model change, so no new
  migration was needed):
  - `apps/accounts/forms.py` — `RegistrationForm` (username, email,
    display name, password twice, email required) and `LoginForm`,
    both with Bootstrap styling on every field.
  - `apps/accounts/views.py` — `register` saves a new user, signs
    them in straight away and sends them to the home page;
    `logout_view` signs the user out and returns them home.
  - `apps/accounts/urls.py` — `/accounts/register/`,
    `/accounts/login/` (Django's `LoginView`) and `/accounts/logout/`.
  - `config/urls.py` includes the accounts URLs; `config/settings/base.py`
    sets `LOGIN_URL`, `LOGIN_REDIRECT_URL` and `LOGOUT_REDIRECT_URL`
    to send users home after signing in or out.
  - `templates/accounts/register.html` and `templates/accounts/login.html`
    extend `base.html` with Bootstrap forms and error messages.
  - `templates/base.html` navigation now shows "Log in" and
    "Create an account" to visitors, and "Hi, <display name>" plus
    "Log out" to signed-in users.
- README updated: registration, login and logout moved to
  "Features that work now"; the limitations now say the sign-in pages
  work but password reset and profile pages are not built yet. No day
  numbers anywhere in the README.

### Test results (Day 2)
- `python manage.py check` — passed, no issues.
- `python manage.py test` — 10 tests, all passed (2 home/health smoke
  tests + 8 new auth tests in `tests/test_auth.py`).
- `python manage.py makemigrations --check --dry-run` — no changes detected.
- `git diff --check` — clean; no secrets found in the diff.
- New tests cover: the register page loads; registration creates a user
  (username, email, display name, working password) and signs them in;
  mismatched passwords do not create a user; the login page loads; login
  works with good details and fails with a wrong password; the navigation
  shows "Log out" and the user's display name when signed in; logout
  signs the user out and the navigation shows "Log in" again.
- Also verified by hand in the dev shell before committing: register →
  signed in and the home page greets the user by name; logout → signed
  out; wrong password → still signed out; good password → signed in.

### Commits (local only)
- See `git log` in the project repo (2 real commits, in plain English).

### Next steps
- Profile page and password reset flow (the next auth work in the plan).
- Then client records (Client model + CRUD).

## Day 3 — 2026-11-14 (ClientFlow)

### Done
- Profile page at `/accounts/profile/` (login required): shows the
  signed-in user's username, email, display name and date joined, with
  a form to update the display name and email.
  - `apps/accounts/forms.py` — new `ProfileForm`, a ModelForm on the
    custom User model with Bootstrap styling.
  - `apps/accounts/views.py` — new `profile` view (login required,
    saves on POST and shows a success message).
  - `templates/accounts/profile.html` — details plus the update form.
  - `templates/base.html` — "Profile" link in the nav for signed-in
    users, a messages area so the success notice shows, and the stale
    footer line fixed (it still carried a day number; now a plain
    sentence about clients, projects, tasks and invoices arriving).
- Password reset flow using Django's built-in views:
  `/accounts/password-reset/`, `/accounts/password-reset/done/`,
  `/accounts/reset/<uidb64>/<token>/` and `/accounts/reset/done/`,
  with four matching templates under `templates/accounts/` extending
  `base.html` with Bootstrap styling. The login page now links to
  "Forgot your password?". `config/settings/dev.py` sets the console
  email backend so reset links print to the console in development
  (`prod.py` untouched).
- README updated: password reset and profile moved to "Features that
  work now"; the limitations now match the current state. No day
  numbers anywhere in the README.

### Test results (Day 3)
- `python manage.py check` — passed, no issues.
- `python manage.py test` — 19 tests, all passed (10 existing + 9 new
  in `tests/test_profile.py`).
- `python manage.py makemigrations --check --dry-run` — no changes detected.
- `git diff --check` — clean; no secrets found in the diff.
- New tests cover: profile redirects anonymous users to login; a
  signed-in user sees their username, email, display name and date
  joined; updating the display name saves it; the nav shows a Profile
  link when signed in; the login page links to password reset; the
  reset page loads; posting a registered email sends exactly one email
  and redirects to the done page; posting an unregistered email still
  redirects but sends no email; the full reset flow end to end
  (extract the link from the sent email, open it, set a new password,
  then log in with the new password — and the old password no longer
  works).

### Commits (local only)
- See `git log` in the project repo (2 real commits, in plain English).

### Next steps
- Client records (Client model + CRUD), per the plan.

## Day 4 — 2026-11-14 (ClientFlow)

### Done
- Client model in `apps/clients/models.py`: name, email, phone, company,
  notes, owner (foreign key to the custom User, related name `clients`)
  and created/updated timestamps. `__str__` returns the name; clients
  order by name. Migration `apps/clients/migrations/0001_initial.py`.
  Registered in admin with list display, owner filter and search.
- Full CRUD, all login required and owner-only:
  - `apps/clients/views.py` — list (`/clients/`, only the signed-in
    user's own clients, ordered by name), detail, create, update and
    delete. Every lookup filters on `owner=request.user`, so a client
    belonging to someone else answers with a 404 — never a permission
    page and never the other user's data. Create sets the owner to the
    signed-in user; successful create/update/delete show a message.
  - `apps/clients/forms.py` — `ClientForm` (ModelForm with Bootstrap
    styling on every field).
  - `apps/clients/urls.py` — `/clients/`, `/clients/add/`,
    `/clients/<pk>/`, `/clients/<pk>/edit/`, `/clients/<pk>/delete/`,
    wired into `config/urls.py`.
  - Templates under `templates/clients/` extending `base.html`:
    `list.html` (with a "No clients yet" empty state), `detail.html`,
    `form.html` (shared by create and edit), `confirm_delete.html`.
  - `templates/base.html` — "Clients" link in the nav for signed-in
    users.
- README updated: client records moved to "Features that work now";
  the planned list and limitations now match the current state. No day
  numbers anywhere in the README.

### Test results (Day 4)
- `python manage.py check` — passed, no issues.
- `python manage.py test` — 36 tests, all passed (19 existing + 17 new
  in `tests/test_clients.py`).
- `python manage.py makemigrations --check --dry-run` — no changes detected.
- `git diff --check` — clean; no secrets found in the diff.
- New tests cover: the list redirects anonymous users to login; the
  empty list shows "No clients yet"; the list shows only the signed-in
  user's clients and hides the other user's; the list is ordered by
  name; the nav shows a Clients link when signed in; creating a client
  saves it under the signed-in user and redirects to its detail page;
  creating without a name saves nothing; the detail page shows the
  client's details; detail, update and delete of another user's client
  all answer with a 404 and change nothing; updating saves the changes;
  delete asks for confirmation, then removes the client and returns to
  the list; `str(client)` returns the name; the owner relationship
  works from the user side.

### Commits (local only)
- See `git log` in the project repo (3 real commits, in plain English).

### Next steps
- Task records (Task model + CRUD, linked to clients), per the plan.

## Day 5 — 2026-11-15 (ClientFlow)

### Done
- Client list search, company filter and pagination on `/clients/`,
  all owner-scoped — search and filter only ever see the signed-in
  user's own clients:
  - `apps/clients/views.py` — `client_list` now reads a `q` query
    parameter and matches it case-insensitively against name, company
    and email, and a `company` parameter that narrows the list to one
    company. The company dropdown is built from the signed-in user's
    own distinct companies. Results are paginated at 10 clients per
    page with `Paginator.get_page`, so an out-of-range page shows the
    last page instead of an error. The page links carry the current
    search and filter along.
  - `templates/clients/list.html` — search box and company dropdown
    in a Bootstrap form that keeps the entered values, a result count
    ("1 client", "12 clients"), Bootstrap pagination controls with
    Previous/Next and page numbers, and two empty states: "No clients
    yet" when the user has no clients at all, and "No clients match
    your search" with a "Show all clients" link when a search or
    filter finds nothing.
- README updated: client list search, filter and pagination moved to
  "Features that work now"; the planned list and limitations now match
  the current state. No day numbers anywhere in the README.

### Test results (Day 5)
- `python manage.py check` — passed, no issues.
- `python manage.py test` — 52 tests, all passed (36 existing + 16 new
  in `tests/test_client_search.py`).
- `python manage.py makemigrations --check --dry-run` — no changes detected.
- `git diff --check` — clean; no secrets found in the diff.
- New tests cover: search finds by name, by company and by email;
  search is case-insensitive; search with no match shows the
  "No clients match your search" state; the company filter narrows
  the list correctly; the company dropdown only lists the user's own
  companies and filtering by a company the user does not have shows
  nothing; search and filter combined (matching and non-matching);
  the search box and filter keep their values after submitting;
  the first page shows 10 clients and page 2 shows the rest; page
  links keep the search parameter; an out-of-range page shows the
  last page; search, filter and pagination never show another user's
  clients; search and filter pages still redirect anonymous users
  to login.
- One test needed a fix during the run: the anonymous-redirect test
  first expected `?next=/clients/`, but Django keeps the query string
  in the redirect (`?next=/clients/%3Fq%3DSara`); the expectation was
  corrected and all 52 tests pass.

### Commits (local only)
- See `git log` in the project repo (3 real commits, in plain English).

### Next steps
- Project records (Project model + CRUD, linked to clients), per the plan.

## Day 6 — 2026-11-16 (ClientFlow)

### Done
- Task model in `apps/tasks/models.py`: title, description, status
  (to do / in progress / done), optional due date, linked client
  (foreign key to `apps.clients.Client`, related name `tasks`) and
  owner (foreign key to the custom User, related name `tasks`) with
  created/updated timestamps. `__str__` returns the title; tasks
  order by newest first. Migration `apps/tasks/migrations/0001_initial.py`.
  Registered in admin with list display, status and owner filters and
  search.
- Full CRUD, all login required and owner-only:
  - `apps/tasks/views.py` — list (`/tasks/`, only the signed-in
    user's own tasks, soonest due date first with tasks that have no
    due date last, then newest first), detail, create, update and
    delete. Every lookup filters on `owner=request.user`, so a task
    belonging to someone else answers with a 404 — never a permission
    page and never the other user's data. Create sets the owner to the
    signed-in user; successful create/update/delete show a message.
  - `apps/tasks/forms.py` — `TaskForm` (ModelForm with Bootstrap
    styling on every field, a date picker for the due date). The form
    takes the signed-in user and only offers that user's own clients
    in the client dropdown, so a task can never be attached to
    another user's client — posting another user's client id is
    rejected by the form and saves nothing.
  - `apps/tasks/urls.py` — `/tasks/`, `/tasks/add/`,
    `/tasks/<pk>/`, `/tasks/<pk>/edit/`, `/tasks/<pk>/delete/`,
    wired into `config/urls.py`.
  - Templates under `templates/tasks/` extending `base.html`:
    `list.html` (status badges and due dates, with a "No tasks yet"
    empty state), `detail.html` (with a link to the linked client),
    `form.html` (shared by create and edit), `confirm_delete.html`.
  - `templates/base.html` — "Tasks" link in the nav for signed-in
    users.
- README updated: task records moved to "Features that work now";
  the planned list and limitations now match the current state. No day
  numbers anywhere in the README.

### Test results (Day 6)
- `python manage.py check` — passed, no issues.
- `python manage.py test` — 71 tests, all passed (52 existing + 19 new
  in `tests/test_tasks.py`).
- `python manage.py makemigrations --check --dry-run` — no changes detected.
- `git diff --check` — clean; no secrets found in the diff.
- New tests cover: the list redirects anonymous users to login; the
  empty list shows "No tasks yet"; the list shows only the signed-in
  user's tasks and hides the other user's; the list is ordered by due
  date with tasks that have no due date last; the nav shows a Tasks
  link when signed in; creating a task saves it under the signed-in
  user and redirects to its detail page; creating without a title
  saves nothing; the client dropdown only lists the user's own
  clients; creating with another user's client is rejected and saves
  nothing; the detail page shows the task's details; detail, update
  and delete of another user's task all answer with a 404 and change
  nothing; updating saves the changes; updating with another user's
  client is rejected; delete asks for confirmation, then removes the
  task and returns to the list; `str(task)` returns the title; the
  owner and the client can both reach the task from their side.

### Commits (local only)
- See `git log` in the project repo (3 real commits, in plain English).

### Projects and task priority/assignee (same day, later)
- Project model in `apps/projects/models.py`: name, description, status
  (active / on hold / completed), start and due dates, linked client
  (foreign key to `apps.clients.Client`, related name `projects`) and
  owner (foreign key to the custom User, related name `projects`) with
  created/updated timestamps. `__str__` returns the name; projects
  order by name. Migration `apps/projects/migrations/0001_initial.py`.
  Registered in admin with list display, status and owner filters and
  search.
- Full project CRUD, all login required and owner-only, following the
  same pattern as clients and tasks:
  - `apps/projects/views.py` — list (`/projects/`, only the signed-in
    user's own projects, ordered by name), detail, create, update and
    delete. Every lookup filters on `owner=request.user`, so a project
    belonging to someone else answers with a 404. Create sets the owner
    to the signed-in user; successful create/update/delete show a message.
  - `apps/projects/forms.py` — `ProjectForm` (ModelForm with Bootstrap
    styling, date pickers for the dates). The form takes the signed-in
    user and only offers that user's own clients in the client dropdown,
    so a project can never be attached to another user's client.
  - `apps/projects/urls.py` — `/projects/`, `/projects/add/`,
    `/projects/<pk>/`, `/projects/<pk>/edit/`, `/projects/<pk>/delete/`,
    wired into `config/urls.py`.
  - Templates under `templates/projects/` extending `base.html`:
    `list.html` (status badges and due dates, with a "No projects yet"
    empty state), `detail.html` (with a link to the linked client),
    `form.html` (shared by create and edit), `confirm_delete.html`.
  - `templates/base.html` — "Projects" link in the nav for signed-in
    users. `templates/clients/detail.html` now lists that client's
    projects with links.
- Task priority and assignee, added to the existing Task model (which
  was built earlier the same day, linked to clients):
  - `apps/tasks/models.py` — `Priority` (low / medium / high, default
    medium) and `assignee` (foreign key to the custom User, may be
    empty, `SET_NULL` so deleting a user keeps their tasks),
    migration `apps/tasks/migrations/0002_task_assignee_task_priority.py`.
  - `apps/tasks/forms.py` — the form now offers priority and assignee;
    priority falls back to medium when a post leaves it out, so older
    posts without it still save.
  - `apps/tasks/admin.py` — priority and assignee in the list display
    and filters. `templates/tasks/list.html` shows a priority badge
    next to the status badge; `templates/tasks/detail.html` shows the
    priority and the assignee (or a dash when there is none).
- Note: the plan's task design links tasks to projects, but the Task
  model was already built, tested and committed earlier the same day
  linked to clients (19 tests), so tasks keep their client link and
  gained priority and assignee instead of being rebuilt around
  projects. Whether tasks should also link to projects is a decision
  for a later day.

### Test results (projects + task fields)
- `python manage.py check` — passed, no issues.
- `python manage.py test` — 104 tests, all passed (71 existing + 20 new
  in `tests/test_projects.py` + 13 new in `tests/test_task_fields.py`).
- `python manage.py makemigrations --check --dry-run` — no changes detected.
- `git diff --check` — clean; no secrets found in the diff.
- New project tests cover: the list redirects anonymous users to login;
  the empty list shows "No projects yet"; the list shows only the
  signed-in user's projects and hides the other user's; the list is
  ordered by name; the nav shows a Projects link when signed in;
  creating a project saves it under the signed-in user and redirects
  to its detail page; creating without a name saves nothing; the client
  dropdown only lists the user's own clients; creating with another
  user's client is rejected and saves nothing; the detail page shows
  the project's details and its client; detail of another user's
  project answers with a 404; the client detail page lists that
  client's projects; updating saves the changes; update of another
  user's project answers with a 404 and changes nothing; updating with
  another user's client is rejected; delete asks for confirmation,
  then removes the project and returns to the list; delete of another
  user's project answers with a 404 and changes nothing; `str(project)`
  returns the name; the owner and the client can both reach the project
  from their side.
- New task field tests cover: priority defaults to medium; creating
  with high priority saves it; creating without a priority saves
  medium; an invalid priority value saves nothing; updating changes
  the priority; the list shows the priority; the assignee is empty by
  default; creating with a real user as assignee saves it; the detail
  page shows the assignee; a task with no assignee shows a dash;
  creating with a made-up user id is rejected and saves nothing;
  updating clears the assignee; deleting the assignee keeps the task
  with no assignee.
- Two real bugs were found and fixed while adding the fields: the
  detail page crashed on a task with no assignee (the template tried
  to read the assignee's name through a filter argument, which Django
  does not forgive — now guarded with an `{% if %}`), and creating or
  updating a task failed when the post left priority out (a required
  choice field with no posted value is invalid — the form now treats
  a missing priority as medium). All 71 older tests pass again after
  the fixes.

### Commits (local only)
- See `git log` in the project repo (4 more real commits, in plain
  English, for the project work and the task fields).

### Next steps
- Invoice records (Invoice and invoice-line models), per the plan.
