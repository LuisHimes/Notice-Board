# Authentication

The backend implements local OAuth2 password-grant login with bearer access tokens.
This is not Google, Microsoft, or other third-party SSO. For organizational SSO,
use an external OpenID Connect provider with Authorization Code and PKCE; that
integration requires your provider choice and registration details and is not
implemented here.

## Operator Setup

No real signing secret or HR credentials have been created. From the project root:

```sh
cd backend
. .venv/bin/activate
pip install -r requirements-dev.txt
export JWT_SECRET_KEY="$(openssl rand -hex 32)"
python bootstrap_hr.py --name "People Team" --email hr@example.com
uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

The bootstrap command prompts for a password and confirmation using hidden terminal
input. Passwords must contain 12-128 characters. It creates an HR account or provisions
initial credentials on an existing HR record. It refuses to convert other roles or
reset an account that already has credentials. No public signup/bootstrap API exists.

The generated shell key is development-only and lasts for the current shell. For
persistent deployments, configure a stable, high-entropy key in your secret manager
or an ignored `.env` file. Use `.env.example` in the project root as the configuration
template; its signing key is deliberately empty. The API refuses startup without a
key of at least 32 bytes. Do not use the test-only keys found in tests.

Configuration:

| Variable | Default | Purpose |
| --- | --- | --- |
| `JWT_SECRET_KEY` | None, required | HS256 signing key, at least 32 bytes |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `15` | Token lifetime, permitted range 1-60 minutes |
| `JWT_ISSUER` | `notice-board-api` | Required token issuer |
| `JWT_AUDIENCE` | `notice-board-client` | Required token audience |
| `DATABASE_URL` | `sqlite:///./notice_board.db` | Application and credentials database |

Docker Compose reads the signing key from the shell or root `.env` and passes it into
the backend. After configuring it, run `docker compose up --build`. Bootstrap the HR
account in that same database using:

```sh
docker compose exec backend python bootstrap_hr.py --name "People Team" --email hr@example.com
```

Enter real passwords directly in your terminal, never in chat or command-line arguments.
The HTTP preview on port 8001 uses a temporary database and an ephemeral key; it is
not configured with your real accounts or persistent signing key.

## Login and Accounts

Open `/docs` and use **Authorize**. The OAuth2 username is the account's email address.
Swagger obtains a token and sends it to protected endpoints automatically.

API clients submit URL-encoded form data to `POST /api/auth/token` with `username`,
`password`, and `grant_type=password`. The response contains `access_token`,
`token_type: "bearer"`, and `expires_in` in seconds. Login responses use
`Cache-Control: no-store`. Subsequent requests use `Authorization: Bearer <access_token>`.

| Endpoint | Access | Behavior |
| --- | --- | --- |
| `POST /api/auth/token` | Public | Obtain an access token |
| `GET /api/auth/me` | Signed-in user | Read your ID, email, name, and role |
| `PUT /api/auth/accounts/{user_id}/password` | HR only | Provision/reset a password using `{"password":"..."}` |
| `POST /api/auth/password` | Signed-in user | Change password using `current_password` and `new_password` |
| `POST /api/auth/logout` | Signed-in user | Revoke all access tokens for that account |

After HR creates staff or onboards a trainee, provision that user's initial password
with the HR-only account endpoint. Users without credentials cannot log in. Password
hashes are never returned in user views. Communicate initial passwords through your
organization's secure channel; automated invitations and email recovery are not implemented.

Passwords use Argon2id with 19 MiB of memory, two iterations, and one lane. Tokens use
HS256 with a fixed accepted algorithm, validated signature, expiry, issuer, audience,
subject, issuance time, and token version. Roles are loaded from the database on every
request, not trusted from client input or token role claims.

Password changes, HR resets, and logout increment the stored token version and revoke
previous tokens, including tokens from other devices. Log in again afterward. There
are no refresh tokens; expired access tokens require a new login. Changing the signing
key also invalidates all previously issued tokens.

## Workflow Permissions

All workflow APIs require authentication. Only `/`, `/api/health`, `/api/auth/token`,
and generated API documentation remain public.

| Action | Permission |
| --- | --- |
| Create staff, onboard trainees, provision/reset credentials | HR only |
| Browse trainee profiles | HR/managers; trainees can read only their own profile |
| Create cohorts/plans, add cohort members, assign/update plans | Manager, owning the relevant cohort/plan |
| Read plans | HR; owning manager; trainees assigned to that plan |
| List cohorts | HR sees all; managers see their own; trainees see their memberships |
| Read cohort membership | HR or owning manager |
| Read assignments/reports | HR; owning plan manager; assigned trainee |
| Submit progress | Assigned trainee only |
| Give feedback | Owning plan manager only |
| Read/mark notifications | Recipient trainee only |

Existing request bodies retain actor IDs such as `manager_id`, `onboarded_by_id`, and
`trainee_id`. These must match the signed-in account for the corresponding action;
they are consistency checks, not credentials. Read actor IDs from `/api/auth/me`.
Manager/trainee list filtering happens before pagination, rather than filtering
already-paginated results in memory. The same plan does not grant a trainee access
to another trainee's assignment or reports.

Missing/invalid/revoked tokens return 401 with `WWW-Authenticate: Bearer`. Authenticated
requests lacking role or ownership permission return 403. Login failures use the same
error response for unknown accounts, unprovisioned accounts, and incorrect passwords.

The new `credentials` table is created on startup without altering existing user
tables. Existing records retain their IDs and role; they need initial credentials
before login. The regular versioned-migrations requirement still applies to future
schema changes.

## Before Deployment

Operator actions deferred until you return:

- Configure a persistent random signing key and bootstrap the real HR account.
- Confirm your identity provider if Google/Microsoft/organizational SSO is required.
  Register the client and redirect URI with that provider; keep any client secret
  in your secret manager, not chat. Local password login is not that SSO integration.
- Configure HTTPS, login throttling at the gateway, and audit logging before exposing
  this to the internet. This implementation does not include a login rate limiter.
- Integrate login/token handling into the frontend; no frontend login screen was added.

SQLite workflow/security tests pass; PostgreSQL integration has not been tested.