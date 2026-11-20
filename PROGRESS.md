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
  linked to clients (19 tests), so tasks kept their client link and
  gained priority and assignee instead of being rebuilt around
  projects. Sir Awais decided later the same day to link tasks to
  projects instead — see "Task rework" below.

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

## Task rework — 2026-11-16 (tasks linked to projects)

### Why
Sir Awais chose to link tasks to projects instead of clients, matching
the plan's architecture (a project belongs to a client, and its tasks
belong to it). Until this rework tasks were linked straight to a
client, which the Day 6 note above had flagged as an open decision.

### Done
- `apps/tasks/models.py` — the Task model drops the `client` foreign
  key and gains a `project` foreign key to `apps.projects.Project`
  (related name `tasks`). Owner, status, priority, due date, assignee
  and timestamps are unchanged. Migration
  `apps/tasks/migrations/0003_remove_task_client_task_project.py`
  removes the client field and adds the project field outright — there
  is no production data, only test data, so nothing is carried across.
- `apps/tasks/forms.py` — `TaskForm` takes a project instead of a
  client; the dropdown only offers the signed-in user's own projects.
- `apps/tasks/views.py` — the task list and creation now live under
  their project (`/projects/<pk>/tasks/` and
  `/projects/<pk>/tasks/add/`); detail, edit and delete stay at
  `/tasks/<pk>/...`. Every view is login-required and owner-scoped:
  opening another user's project task list or create page answers
  with a 404, and the project in the URL is authoritative when a
  task is created — posting a different project id in the form still
  saves the task under the project in the URL. Deleting a task now
  returns to that project's task list.
- `apps/projects/urls.py` — the nested task list and create routes
  (`task-list`, `task-create`); `apps/tasks/urls.py` keeps only
  detail, update and delete.
- `apps/tasks/admin.py` — project replaces client in the list display
  and filters.
- Templates — `templates/tasks/list.html` is now "Tasks for
  <project>", with an "Add a task" button and a back link to the
  project; `detail.html` shows the project (linked) instead of the
  client; `form.html` cancels back to the project's task list when
  creating; `confirm_delete.html` names the project. The project
  detail page now lists its tasks with status and priority badges and
  an "Add a task" button, so tasks are reached through their project.
  The "Tasks" link was removed from the nav in `templates/base.html` —
  the projects list is the way in to tasks now. The client detail page
  already listed only projects, so it needed no change.
- README updated: task records are now described as linked to a
  project, with the list living under it. No day numbers anywhere in
  the README.

### Test results (rework)
- `python manage.py check` — passed, no issues.
- `python manage.py test` — 108 tests, all passed (104 existing + 4
  new). `tests/test_tasks.py` and `tests/test_task_fields.py` were
  rewritten to build a project first and create tasks under it.
- `python manage.py makemigrations --check --dry-run` — no changes
  detected, so the hand-written migration matches the model state.
- `python manage.py migrate tasks` — applies cleanly on the dev
  database (0001, 0002, 0003).
- `git diff --check` — clean; no secrets found in the diff.
- New tests cover: the task list and create page of another user's
  project answer with a 404; creating under another user's project
  id is rejected; creating with a different project in the form still
  saves the task under the project in the URL; the project detail page
  lists the task and links to it; `project.tasks.all()` reaches the
  task. The older task tests now run against the project link
  (dropdown, update rejection, delete redirect to the project's task
  list, model relations).

### Commits (local only)
- See `git log` in the project repo (3 real commits, in plain
  English).

### Next steps
- Invoice records (Invoice and invoice-line models), per the plan.

## Day 7 — 2026-11-17 (ClientFlow)

### Done
- Dashboard page at `/dashboard/` (login required) that sums up the
  signed-in user's own work — nothing from another user ever appears:
  - New `apps/dashboard/` app (views, URLs, no models, so no new
    migration): `apps/dashboard/views.py` — `dashboard` view, login
    required, everything filtered on `owner=request.user`. It counts
    the user's own clients, projects and tasks; splits tasks by
    status (to do, in progress, done); lists overdue tasks — due date
    in the past and status not done — soonest due first; and shows
    the newest 5 clients, projects and tasks. Registered in
    `config/settings/base.py` and wired in at `dashboard/` in
    `config/urls.py`.
  - `templates/dashboard/dashboard.html` — Bootstrap cards for the
    three counts, a tasks-by-status list with count badges, an
    overdue-tasks list with due dates, and recent clients, projects
    and tasks with links to their detail pages, plus quick links to
    add a client, add a project and open the clients and projects
    lists. Plain-word empty states ("No clients yet", "No projects
    yet", "No tasks yet", "No overdue tasks").
  - `templates/base.html` — "Dashboard" link in the nav for
    signed-in users. `templates/home.html` — an "Open your dashboard"
    button for signed-in users. Tasks stay linked to projects, as
    after the 16 Nov rework: the nav still has no "Tasks" link and
    tasks are still reached through their project.
- README updated: the dashboard moved to "Features that work now" and
  off the planned list; the limitations now match the current state.
  No day numbers anywhere in the README.

### Test results (Day 7)
- `python manage.py check` — passed, no issues.
- `python manage.py test` — 123 tests, all passed (108 existing + 15
  new in `tests/test_dashboard.py`).
- `python manage.py makemigrations --check --dry-run` — no changes detected.
- `git diff --check` — clean; no secrets found in the diff.
- New tests cover: the dashboard redirects anonymous users to login;
  a signed-in user sees the dashboard; counts only include the
  signed-in user's own clients, projects and tasks; the status
  breakdown counts are right; the empty dashboard shows plain empty
  states; the overdue list only has past-due unfinished tasks of that
  user, soonest due first, and leaves out finished, not-yet-due and
  dateless tasks and the other user's overdue tasks; overdue tasks
  link to their detail pages; the recent lists show the user's newest
  five of each and hide the oldest and the other user's items; the
  nav shows Dashboard when signed in and hides it when signed out;
  the home page links to the dashboard when signed in and not when
  signed out; the dashboard quick links work; the dashboard links to
  recent items' detail pages.
- Two test mistakes were found and fixed while running them: the
  recent-lists test first linked every task to the same project, so
  the excluded project's name still showed under the tasks, and the
  overdue test first expected finished and not-yet-due tasks to be
  absent from the whole page, when they rightly appear in the
  recent-tasks list — the checks now look at the overdue section
  itself. The dashboard code was right in both cases.

### Commits (local only)
- See `git log` in the project repo (3 real commits, in plain
  English).

### Next steps
- Invoice records (Invoice and invoice-line models), per the plan.

## Day 8 — 2026-11-18 (ClientFlow)

### Done
- Invoice model in `apps/billing/models.py`: number (unique per
  owner, auto-generated on first save as INV-0001, INV-0002, ...,
  sequential per owner), client (foreign key to
  `apps.clients.Client`, related name `invoices`), optional project
  (foreign key to `apps.projects.Project`, related name `invoices`,
  may be empty), status (draft / sent / paid / overdue, default
  draft), issue date (defaults to today), due date (may be empty),
  owner (foreign key to the custom User, related name `invoices`)
  and created/updated timestamps. `__str__` returns the number;
  invoices order by newest first. Migration
  `apps/billing/migrations/0001_initial.py`. Numbers are unique per
  owner (a `UniqueConstraint` on owner + number), not globally, so
  two users can each have their own INV-0001. `apps/billing` was
  already registered in `config/settings/base.py` `INSTALLED_APPS`,
  so no settings change was needed.
- InvoiceLineItem model in the same file: invoice (foreign key,
  related name `items`, cascade delete), description, quantity
  (Decimal, default 1) and unit price (Decimal). Each line has a
  computed `line_total` property (quantity x unit price), and each
  invoice has a computed `total` property (sum of its items, zero
  when there are none) and an `is_overdue` helper (status not paid
  and due date in the past).
- Invoices in the app, all login required and owner-only:
  - `apps/billing/views.py` — list (`/invoices/`, only the
    signed-in user's own invoices, newest first, with status
    shown), detail (`/invoices/<pk>/`, shows client, project if
    any, dates, status, line items with line totals and the invoice
    total), create (`/invoices/add/`, with an inline formset so
    line items are added on the same page — at least one line item
    is required). Every lookup filters on `owner=request.user`, so
    another user's invoice answers with a 404. Successful create
    shows a message and redirects to the detail page.
  - `apps/billing/forms.py` — `InvoiceForm` (ModelForm with
    Bootstrap styling, date pickers for the dates). The form takes
    the signed-in user and only offers that user's own clients and
    projects in the dropdowns, so an invoice can never be attached
    to another user's client or project — posting another user's
    client or project id is rejected by the form and saves nothing.
  - `apps/billing/urls.py` — `/invoices/`, `/invoices/add/`,
    `/invoices/<pk>/`, wired into `config/urls.py`.
  - Templates under `templates/invoices/` extending `base.html`:
    `list.html` (status badges, with a "No invoices yet" empty
    state), `detail.html` (line-item table with line totals and
    the invoice total), `form.html` (invoice fields plus the line
    item formset).
  - `templates/base.html` — "Invoices" link in the nav for
    signed-in users.
  - `apps/billing/admin.py` — both models registered; invoices
    show number, client, status, dates and owner, with status and
    owner filters and search; line items are editable inline on
    the invoice page.

### Test results (Day 8)
- `python manage.py check` — passed, no issues.
- `python manage.py test` — 148 tests, all passed (123 existing +
  25 new in `tests/test_invoices.py`).
- `python manage.py makemigrations --check --dry-run` — no changes detected.
- `git diff --check` — clean; no secrets found in the diff.
- New tests cover: the list redirects anonymous users to login; the
  empty list shows "No invoices yet"; the list shows only the
  signed-in user's invoices and hides the other user's; the nav shows
  an Invoices link when signed in; creating an invoice saves it under
  the signed-in user with its line items and the total is right
  (2 x 10.00 + 3 x 5.50 = 36.50) and redirects to its detail page;
  creating without a client saves nothing; creating without any line
  items saves nothing; the client dropdown only lists the user's own
  clients and the project dropdown only their own projects; creating
  with another user's client or project is rejected and saves
  nothing; the detail page shows the items, their line totals and
  the invoice total; detail of another user's invoice answers with a
  404; `str(invoice)` returns the number; numbers run in sequence
  per owner (INV-0001, INV-0002) and restart per owner; line total
  math (2.5 x 19.99 = 49.975, including decimals); an invoice with no
  line items totals zero; the total sums all line items; the overdue
  helper is true only when unpaid and past due (paid, future-due and
  dateless invoices are not overdue); the owner and the client can
  both reach the invoice from their side.
- One test mistake was found and fixed while running them: the
  create-without-a-client test passed the client argument twice to
  its helper, which raised a TypeError — the helper call was fixed
  and all 25 new tests pass.

### Commits (local only)
- See `git log` in the project repo (3 real commits, in plain
  English).

### Next steps
- Invoice editing, status changes and deletion, per the plan.

## Day 9 — 2026-11-19 (ClientFlow)

### Done
- Invoice editing at `/invoices/<pk>/edit/` (login required,
  owner-only):
  - `apps/billing/views.py` — `invoice_update` edits the invoice
    fields (client, project, status, dates) and its line items on
    one page, with the same owner-scoped form as create, so an
    invoice can never be attached to another user's client or
    project. Successful edit shows a message and returns to the
    detail page; editing another user's invoice answers with a 404.
  - `apps/billing/forms.py` — new `InvoiceLineItemEditFormSet`,
    the same as the create formset except line items can be removed.
    At least one item must still remain: removing every item is
    rejected, because an invoice with no lines cannot be saved.
  - `templates/invoices/form.html` — now shared by create and
    edit: the title and button read "Edit <number>" / "Save changes"
    when editing, and "Add an invoice" / "Add invoice" when creating.
  - `templates/invoices/detail.html` — "Edit invoice" and "Delete
    invoice" buttons.
- Invoice deletion at `/invoices/<pk>/delete/` (login required,
  owner-only): `invoice_delete` shows a confirm page
  (`templates/invoices/confirm_delete.html`), then deletes the
  invoice and its line items and returns to the list with a message.
  Deleting another user's invoice answers with a 404 and changes
  nothing.
- One-click status changes on the invoice detail page (POST only,
  owner-only):
  - `apps/billing/models.py` — `ALLOWED_STATUS_CHANGES` and a
    `can_move_to` helper, with the rules written down in the code:
    draft can move to sent or paid, sent and overdue can move to
    paid, and paid is final — a paid invoice cannot be reopened.
    Overdue is set from the edit form, never by a one-click button;
    the edit form sets the status directly and does not enforce
    these transitions.
  - `apps/billing/views.py` — `invoice_status_change` at
    `/invoices/<pk>/status/`. A GET (or any non-POST) changes
    nothing and returns to the detail page. An unknown status or a
    move that is not allowed changes nothing and shows an error
    message. A valid move saves the new status and shows a success
    message.
  - `templates/invoices/detail.html` — "Mark as sent" and
    "Mark as paid" buttons on a draft invoice, "Mark as paid" on a
    sent or overdue invoice, and no status buttons on a paid one.
- Invoice list status filter and CSV export:
  - `apps/billing/views.py` — `invoice_list` now reads a `status`
    query parameter and narrows the list to one status; an unknown
    value is ignored and the full list is shown.
    `invoice_export_csv` at `/invoices/export/` downloads the
    signed-in user's own invoices as a CSV file (number, client,
    project — blank when there is none, status, issue date, due
    date, total), following the same status filter. Totals are
    written with two decimal places. Another user's invoices never
    appear.
  - `templates/invoices/list.html` — status dropdown with a Filter
    button and a "Show all" link, a "Download as CSV" button that
    keeps the current filter, and a "No invoices with this status"
    empty state when a filter matches nothing.
- README updated: invoice records, status changes, the list filter
  and CSV export moved to "Features that work now" (the invoice
  creation from the previous day had not been added to the README
  yet, so it is added here too); the planned list now only carries
  what is still missing (invoice tax/discount, CSV export for
  clients); the limitations now match the current state. No day
  numbers anywhere in the README.

### Test results (Day 9)
- `python manage.py check` — passed, no issues.
- `python manage.py test` — 181 tests, all passed (148 existing +
  33 new in `tests/test_invoice_actions.py`).
- `python manage.py makemigrations --check --dry-run` — no changes detected.
- `git diff --check` — clean; no secrets found in the diff.
- New tests cover: the edit page loads and shows the invoice and its
  items; editing saves field and line-item changes and redirects to
  the detail page; editing can add a line item and can remove one;
  editing that removes every line item saves nothing; edit, delete
  and status change of another user's invoice all answer with a 404
  and change nothing; editing with another user's client is rejected;
  delete asks for confirmation, then removes the invoice and its
  items and returns to the list; draft can be marked sent or paid,
  sent and overdue can be marked paid, paid cannot go back to sent
  or overdue, sent cannot go back to draft, an unknown status changes
  nothing, and a GET request changes nothing; the detail page offers
  the right buttons for each status; the list filter narrows to one
  status, never shows another user's invoices, ignores an unknown
  status and shows a filtered empty state; the CSV download has the
  right headers and one row per invoice with the right values
  (including a blank project and a blank due date), never includes
  another user's invoices, follows the status filter, returns only
  the header row when the user has no invoices, and redirects
  anonymous users to login.
- Two test mistakes were found and fixed while running them: the
  CSV total first came out as "16.5000" because the raw Decimal
  keeps four decimal places — the export now writes totals with two
  decimal places; and the other-user CSV check first compared
  invoice numbers, which restart per owner (both users have their
  own INV-0001) — the check now looks for the other user's client
  name instead. The export code was right in the second case.

### Commits (local only)
- See `git log` in the project repo (4 real commits, in plain
  English).

### Next steps
- Sample data command and security review, per the plan.

## Day 10 — 2026-11-20 (ClientFlow)

### Done
- Sample data command `seed_demo_data` in
  `apps/dashboard/management/commands/seed_demo_data.py` — one
  command populates the app for a new developer:
  - Creates a demo user (`demo`, `demo@example.com`, password
    `DemoPass123!`) with 3 clients (Sara Ahmed / The Bakehouse,
    Bilal Khan / Print House, Ayesha Malik / Ayesha Events),
    4 projects, 8 tasks across the projects (a mix of done, in
    progress and to-do, with one overdue task) and 3 invoices in
    draft, sent and paid states, with 5 line items between them.
  - Safe and honest by design: it refuses to run when DEBUG is off
    unless given `--force`, so demo data can never land in a real
    deployment by accident; `--clear` deletes the demo user first
    and the database cascades that to only the demo user's clients,
    projects, tasks and invoices — nobody else's data is touched.
  - Idempotent: every record is created with `get_or_create`
    keyed on the demo user and its natural fields (client name,
    project name, task title, invoice client and project), so a
    second run reports 0 new records and changes nothing.
  - Prints a short plain-English summary of what it created
    ("Demo data ready: 3 clients (3 new), ...") and, when the demo
    user is new, the login details.
  - Verified by hand in development: first run creates everything,
    second run creates nothing, `--clear` wipes the demo data and
    seeds it fresh.
- Security review — `manage.py check --deploy` run against the real
  production settings, plus a manual audit of every view and the
  settings files. Findings and fixes:
  - HSTS was missing (warning W004): production settings now set
    `SECURE_HSTS_SECONDS` to one year with
    `SECURE_HSTS_INCLUDE_SUBDOMAINS`. Preload stays off on purpose
    — joining the browser preload list is hard to undo — and the
    deploy check's remaining W021 warning about that is recorded
    in the tests as the one accepted warning.
  - A short secret key was accepted in production (warning W009
    only fired for the test key): production settings now refuse
    to start with a key under 50 characters, as well as with no
    key at all.
  - The shared base settings carried a fallback secret key that a
    deployment pointed at the base settings would have used with
    DEBUG off: base settings now refuse to start without a key
    when DEBUG is off, and the clearly-marked unsafe dev key is
    only used when DEBUG is on. Development settings state this
    before the base settings load.
  - Cookie and header hardening in production settings: CSRF
    cookie hidden from JavaScript (`CSRF_COOKIE_HTTPONLY`, safe
    here because no script reads the cookie — forms carry the
    token), `SECURE_CONTENT_TYPE_NOSNIFF` and a same-origin
    referrer policy set explicitly.
  - Already sound, verified rather than changed: DEBUG is off and
    `ALLOWED_HOSTS` is mandatory in production; all four password
    validators are on; `SecurityMiddleware`,
    `CsrfViewMiddleware` and `XFrameOptionsMiddleware` are in the
    middleware (clickjacking protection defaults to deny);
    `SESSION_COOKIE_SECURE`, `CSRF_COOKIE_SECURE` and
    `SECURE_SSL_REDIRECT` were already set in production.
  - Owner-scoping audit of every view: all client, project, task,
    invoice and dashboard lookups filter on `owner=request.user`
    (checked by reading each view), so no view leaks another
    user's data — the invoice CSV export and the dashboard counts,
    overdue list and recent lists are owner-scoped the same way.
    The profile page only ever touches `request.user`. The
    password-reset email template uses `{% autoescape off %}`,
    which is Django's own standard template for that email and
    carries only the site address, not user input. The admin
    shows all users' records to staff only, which is Django's
    normal admin behaviour.
  - Error pages: there were no custom 404/500 templates, so
    `templates/404.html` and `templates/500.html` were added —
    plain pages that never show a stack trace (verified by tests
    that hit both pages with DEBUG off).
- README updated: the demo data command and the security review
  moved to "Features that work now"; the demo command left the
  planned list; the limitations now warn that the demo command is
  for local development only and the demo password is published.
  No day numbers anywhere in the README.

### Test results (Day 10)
- `python manage.py check` — passed, no issues.
- `python manage.py test` — 194 tests, all passed (181 existing +
  13 new: 7 in `tests/test_seed_demo_data.py`, 6 in
  `tests/test_security.py`).
- `python manage.py makemigrations --check --dry-run` — no changes detected.
- `git diff --check` — clean; no secrets found in the diff.
- `manage.py check --deploy` with the real production settings
  and a proper 50-character key: only the deliberate HSTS-preload
  warning (W021) remains.
- New seed tests cover: the command creates the demo user (with a
  working password) plus 3 clients, 4 projects, 8 tasks, 3 invoices
  and 5 line items, with the records linked correctly; the demo
  user can sign in and sees the seeded clients on the dashboard;
  running twice creates nothing new; `--clear` removes the demo
  user's data (including a record made outside the seed data) and
  reseeds it fresh, while another user's client survives untouched;
  `--clear` with no demo user says so; the command refuses when
  DEBUG is off without `--force` and creates nothing; `--force`
  allows it when DEBUG is off.
- New security tests cover: the deploy check passes with the real
  production settings (only the accepted W021 warning); production
  settings refuse a short key and a missing key; the base settings
  refuse to start without a key when DEBUG is off; the custom 404
  page renders for an unknown address and the custom 500 page
  renders for a failing view, both with DEBUG off and neither
  showing a traceback or the error message.
- Three real test mistakes were found and fixed while running
  them: the seed tests first ran with DEBUG off (the test runner
  forces it off, so the command refused — the tests now switch
  DEBUG back on); the line-item count was 5, not 6 as first
  written; and the 500 test first used a bare test URLconf that
  could not reverse the home page link in the base template, so
  the real URLconf is included in it. The command and the
  settings were right in each case.

### Commits (local only)
- See `git log` in the project repo (3 real commits, in plain
  English).

### Next steps
- Invoice tax and discount, per the plan.
