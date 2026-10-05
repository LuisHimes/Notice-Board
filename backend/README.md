# EdTech Training API

FastAPI backend for HR onboarding, cohort and solo training plans, progress reports,
manager feedback, and persistent in-app notifications. Existing `/` and
`/api/health` endpoints are preserved.

## Architecture

- **Models:** `app/models/` contains one SQLAlchemy model module per domain object.
- **Views:** `app/schemas/` defines domain-specific request bodies and JSON response views.
- **Controllers:** `app/controllers/` contains domain routers that call injected services.
- **Services:** `app/services/` separates onboarding, cohorts, membership, plans,
   assignments, progress reports, and notification rules.
- **Repositories:** `app/repositories/` contains domain queries and shared persistence
   operations in `base.py`.
- **Dependency injection:** `app/dependencies/` contains a service provider per domain
   and shared repository providers in `repositories.py`. These wire the request-scoped
   database session into repositories and services using FastAPI `Depends`. Cross-domain
   services are injected too, rather than instantiated inside workflow methods.
  Dependencies can be replaced with `app.dependency_overrides` for tests.
- **Application setup:** `main.py` exposes `create_app()` to assemble middleware,
   exception handlers, and routers. `app = create_app()` preserves the existing
   `uvicorn main:app` entry point. Welcome and health endpoints live in
   `app/controllers/system.py`.

The layout is `app/<layer>/<domain>.py`. For example, assignment behavior lives in:

```text
app/
   controllers/assignment.py
   dependencies/assignment.py
   models/assignment.py
   repositories/assignment.py
   schemas/assignment.py
   services/assignment.py
   database.py
```

Each layer also has modules for users, cohorts, membership, plans, progress reports,
and notifications. Controllers distinguish staff and trainee routes; both share the
existing user model and onboarding service. Shared base classes and pagination types
live in `base.py` or `common.py` within the relevant layer. Package `__init__.py`
files expose imports and compose routers; they do not contain domain workflows.
The generic `BaseService` retains each domain's repository type, so subclasses do
not need to initialize or reassign their repository twice. Dependency providers
use explicit keyword arguments when composing services.

FastAPI caches dependencies within a request, so all injected repositories use the
same session. Notification creation stages a write without committing; the owning
workflow commits the complete operation. Table names, columns, API routes, and JSON
schemas are unchanged by this layout, so no database migration is required.

Authentication adds a separate `credentials` table, created on startup without
altering existing user records. OAuth2 login, password management, and authorization
each have their own schemas, services, repositories, and dependency providers.

Assignments and their notifications are saved in one transaction. Updating a plan
notifies every assigned trainee. Manager feedback also generates a notification.

## Run Locally

From the project root:

```sh
cd backend
python3 -m venv .venv
. .venv/bin/activate
pip install -r requirements-dev.txt
export JWT_SECRET_KEY="$(openssl rand -hex 32)"
python bootstrap_hr.py --name "People Team" --email hr@example.com
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

- Interactive Swagger documentation: http://localhost:8000/docs
- OpenAPI schema: http://localhost:8000/openapi.json
- Default persistence: SQLite file `notice_board.db` in the working directory.
- Set `DATABASE_URL` to a SQLAlchemy PostgreSQL connection URL to use PostgreSQL.
- Set `CORS_ORIGINS` to a comma-separated list of permitted frontend origins.
  Defaults: `http://localhost:3000,http://localhost`.
- A local `.env` file is supported via python-dotenv.
- `JWT_SECRET_KEY` is required; the API fails startup if it is absent or too short.
   Use a stable key from your secret manager for persistent deployments.

Alternatively, run `docker compose up --build` from the project root. Compose
configures PostgreSQL and waits for its health check before starting the backend.
The signing key must be supplied in the shell or root `.env` first. See
[Authentication](AUTHENTICATION.md) for local and Docker HR bootstrap commands.

Tables are created on application startup. This bootstraps a fresh database;
it does not migrate existing tables. Use versioned migrations before evolving
a deployed database schema.

## Workflow

Use Swagger's **Authorize** control to sign in with the bootstrap HR account before
onboarding. HR must provision each new user's password through
`PUT /api/auth/accounts/{user_id}/password`. Sign in as the relevant manager or trainee
before their workflow steps, and use that user's ID from `/api/auth/me` in request
bodies. Full account setup and permission rules are in [Authentication](AUTHENTICATION.md).

Execute the following requests, substituting returned IDs:

1. Create HR and manager records using `POST /api/staff`:
   `{"name":"People Team","email":"hr@example.com","role":"hr"}` and
   `{"name":"Training Manager","email":"manager@example.com","role":"manager"}`.
2. HR onboards a trainee using `POST /api/trainees`:
   `{"name":"New Trainee","email":"trainee@example.com","onboarded_by_id":1}`.
3. Create a cohort using `POST /api/cohorts`:
   `{"name":"October Cohort","manager_id":2}`.
4. Add trainees using `POST /api/cohorts/{cohort_id}/members`:
   `{"trainee_id":3}`.
5. Create a plan using `POST /api/plans`:
   `{"title":"Python Foundations","description":"Complete modules 1-3","manager_id":2}`.
6. Assign the plan using `POST /api/plans/{plan_id}/assignments`:
   `{"cohort_id":1}` for a cohort, or `{"trainee_id":3}` for a solo track.
   Optional `due_date` accepts an ISO 8601 datetime.
7. Trainees fetch `/api/trainees/{trainee_id}/assignments` and
   `/api/trainees/{trainee_id}/notifications`.
8. Submit progress using `POST /api/assignments/{assignment_id}/reports`:
   `{"trainee_id":3,"progress":50,"summary":"Completed the first module"}`.
9. Review progress using `GET /api/assignments/{assignment_id}/reports` and
   `PATCH /api/reports/{report_id}/feedback`:
   `{"manager_id":2,"feedback":"Continue with module two"}`.
10. Update a plan using `PATCH /api/plans/{plan_id}`:
    `{"description":"Complete modules 1-4"}`. Assigned trainees are notified.
11. Mark a notification read using
    `PATCH /api/trainees/{trainee_id}/notifications/{notification_id}/read`.

List endpoints support `offset` (default 0) and `limit` (default 100, maximum 100).
Other lookup routes include `GET /api/trainees/{trainee_id}`, `GET /api/plans/{plan_id}`,
`GET /api/trainees`, `GET /api/plans`, `GET /api/cohorts`, and
`GET /api/cohorts/{cohort_id}/members`.

## Rules and Boundaries

- Only the authenticated HR user can act as a trainee's onboarding owner.
- Cohorts and plans must reference manager records; cohort assignments require
  the cohort and plan to share a manager.
- Cohort assignments snapshot current membership. Later members do not receive
  existing plans automatically; assign those plans to them separately.
- Each trainee can receive a given plan once, whether through a cohort or solo track.
  A conflicting cohort assignment is rejected entirely, without partial writes.
- Progress is an integer from 0 to 100. The latest submitted report updates the
  assignment's current progress; earlier reports remain in the history.
- Only the authenticated assigned trainee can submit a report, and only the plan's
   authenticated manager can provide feedback. Client-supplied actor IDs cannot
   impersonate another account.
- Missing records return 404, role/ownership mismatches 403, duplicates 409,
  invalid workflow operations 400, and invalid request bodies 422.
- Notifications are stored for polling. Email, push delivery, and WebSockets are not implemented.

**Security:** Workflow endpoints use OAuth2 bearer authentication with role/ownership
checks. Local login uses Argon2id password hashes and short-lived, revocable JWTs;
this is not external-provider SSO. Configure real secrets, bootstrap HR, and add HTTPS,
login throttling, and audit logging before deployment. See
[Authentication](AUTHENTICATION.md) for details and deferred operator actions.

## Tests

From `backend`, after installing `requirements-dev.txt`:

```sh
python -m unittest -v test_api
```

Tests create an isolated application with a no-op lifespan and override its database
dependency with an in-memory SQLite database. Test clients and engines use automatic
cleanup, including when setup fails; no test mutates the global application's
dependency overrides or lifespan. Foreign keys are enabled, and the configured
application database is never used. Tests cover onboarding,
cohort and solo assignments, updates, notifications, report history, feedback,
pagination, validation, role/ownership rules, and atomic duplicate rejection.
They also verify that the domain dependency graph shares a single overridden
database session and reuses service dependencies within a request.
An application-factory regression verifies that overrides stay isolated and that
separate app instances expose the same API schema.
Security tests use real password hashes and signed tokens and cover login, expiry,
tampering, database-backed roles, anonymous route access, impersonation, cross-record
access, scoped pagination, password-reset/logout revocation, and existing-user bootstrap.
PostgreSQL integration is not covered by these SQLite tests.