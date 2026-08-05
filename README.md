# Django Metete Backend

A Django REST Framework backend service providing authentication, role/permission management, media uploads, location data, and notifications, with Celery-powered background tasks and Redis caching.

## Tech Stack

- **Framework:** Django 5.2 + Django REST Framework
- **Auth:** JWT (`djangorestframework-simplejwt`), custom JWT auth middleware, Google/Apple/Facebook social auth
- **Database:** PostgreSQL (SQLite available for local/test use)
- **Cache / Broker:** Redis (`django-redis`, Celery broker & result backend)
- **Background jobs:** Celery (with dedicated `notification`, `logging`, and `default` queues)
- **Realtime:** Django Channels (ASGI, via Daphne)
- **Storage:** AWS S3 (`django-storages`) or local media
- **Email:** SMTP (Zoho/SSL) and Mailjet
- **Admin UI:** django-jazzmin

## Project Structure

```
core/               # Django project settings, URL root, ASGI/WSGI, Celery app
account/            # Users, auth (login, OTP, 2FA, password reset), social auth, profile
roles_permissions/  # Roles and permissions
base/               # Shared app-level defaults, mail sender, seeding
location/           # Countries, states, cities
media/              # Media types, upload/delete
notification/       # Notification templates and dispatch (email etc.), Celery tasks
utils/              # Shared middleware, custom response renderer, encryption, errors, constants
api/v1.py           # Top-level API v1 route aggregator
```

Each domain app follows a `v1/` sub-structure with `views/`, `serializers/`, `services/`, and `urls/` where applicable.

## Prerequisites

- Python 3.11+ (developed against 3.13)
- PostgreSQL (unless using the SQLite test DB)
- Redis (required — used for cache, Celery broker, and Channels layer)

## Setup

### 1. Clone and create a virtual environment

```bash
mkdir <project-name>
cd <project-name>
git clone https://github.com/nodebe/django-metete-v2.git .
python3 -m venv .venv
source .venv/bin/activate
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure environment variables

Copy the example env file and fill in your own values:

```bash
cp env.example .env
```

Key variables to set:

| Variable | Purpose |
|---|---|
| `SECRET_KEY` | Django secret key |
| `DEBUG` | `True`/`False` |
| `ALLOWED_HOSTS`, `CORS_ALLOWED_ORIGINS`, `CSRF_TRUSTED_ORIGINS` | Connection/security allowlists |
| `USE_TEST_DB` | `True` to use local SQLite instead of Postgres |
| `DB_NAME`, `DB_USERNAME`, `DB_PASSWORD`, `DB_HOST`, `DB_PORT` | PostgreSQL connection (ignored if `USE_TEST_DB=True`) |
| `REDIS_HOST`, `REDIS_PREFIX` | Redis connection URL and cache/queue key prefix |
| `ADMIN_EMAIL`, `ADMIN_PASSWORD`, `ADMIN_PHONE_NUMBER` | Used to seed the first superadmin |
| `EMAIL_HOST`, `EMAIL_HOST_USER`, `EMAIL_HOST_PASSWORD`, `EMAIL_PORT` | SMTP settings for outbound email |
| `MJ_API_KEY`, `MJ_API_SECRET` | Mailjet credentials |
| `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `AWS_STORAGE_BUCKET_NAME`, `AWS_S3_REGION_NAME`, `USES_S3_BUCKET` | S3 media storage (set `USES_S3_BUCKET=False` to serve media locally) |
| `SOCIAL_AUTH_GOOGLE_OAUTH2_KEY_WEB`, `APPLE_CLIENT_ID`, `APPLE_CLIENT_SECRET` | Social login credentials |

For local development, the quickest path is `USE_TEST_DB="True"` (SQLite) and `USES_S3_BUCKET="False"` so you don't need Postgres or AWS credentials to get started. Redis is still required.

### 4. Run database migrations

```bash
python manage.py makemigrations account base location media notification roles_permissions
python manage.py migrate
```

### 5. Seed default data

The `Makefile` wraps the required management commands to bootstrap roles, an admin user, cities, and media types:

```bash
make setup_defaults
```

This runs, in order:

```bash
python manage.py create_default_permissions
python manage.py create_default_roles
python manage.py create_superadmin --first_admin=True
python manage.py seed_cities --country "Nigeria"
python manage.py seed_default_media_type
```

You can also run any of these individually, or via their `make` targets: `make default_roles`, `make default_admin`, `make seed_default_cities`, `make default_media_types`.

> `create_superadmin --first_admin=True` uses `ADMIN_EMAIL` / `ADMIN_PASSWORD` / `ADMIN_PHONE_NUMBER` from your `.env`. To create additional admins: `python manage.py create_superadmin --email=admin@email.com --password=Default@123 --username=admin_name`.

### 6. Run the development server

```bash
python manage.py runserver
```

The API is served at `http://127.0.0.1:8000/api/v1/` by default, and the Django admin at `/sys-admin-path/`.

### 7. Run Celery (background jobs)

In separate terminals (with the same environment activated):

```bash
# Worker consuming all queues, with beat scheduler
celery -A core worker -l info -B

# Or run per-queue workers
celery -A core worker -l info -Q default -c 4 -n default
celery -A core worker -l info -Q notification -c 4 -n notification
celery -A core worker -l info -Q logging -c 4 -n logging
```

Celery uses `REDIS_HOST` as both broker and result backend, so Redis must be running first.

## API Overview

All endpoints are mounted under `/api/v1/`:

| Path | App | Purpose |
|---|---|---|
| `auth/` | `account` | Login, password reset/forgot, OTP verification, 2FA, token refresh |
| `profile/` | `account` | Authenticated user profile, password settings |
| `users/` | `account` | User management (list/create/retrieve/update/activate) |
| `roles/` | `roles_permissions` | Roles and permissions |
| `media/` | `media` | Media types, upload, delete |
| `location/` | `location` | Countries, states, cities |

Authentication is JWT-based (bearer token) via `djangorestframework-simplejwt`, with access tokens valid for 1 day and refresh tokens for 10 days (see `SIMPLE_JWT` in `core/settings.py`).

### Response format

All responses (success and error) are normalized by `utils.middlewares.CustomResponseRenderer`:

```json
// Success
{
  "success": true,
  "message": "Record(s) fetched successfully.",
  "data": { },
  "meta": { "timestamp": "..." }
}

// Paginated success
{
  "success": true,
  "message": "...",
  "data": [ ],
  "meta": {
    "page_size": 10, 
    "current_page": 1, 
    "last_page": 3,
    "total": 25, 
    "next_page_url": "...", 
    "prev_page_url": null,
    "timestamp": "..."
  }
}

// Error
{
  "success": false,
  "message": "Resource not found",
  "error": { "field": "email", "label": "invalid_data" },
  "meta": { "timestamp": "..." }
}
```

## Useful Commands

```bash
python manage.py createsuperuser         # standard Django admin user
python manage.py create_superadmin       # app-level superadmin (see above)
python manage.py makemigrations
python manage.py migrate
python manage.py test                    # run tests
python manage.py shell
```

## Notes

- `AUTH_USER_MODEL` is `account.User` — a custom user model.
- Set `APP_ENC_ENABLED=True` and configure `APP_ENC_KEY`/`APP_ENC_VEC` if you need response payload encryption (see `CustomResponseRenderer`).
- The Django admin is exposed at `/sys-admin-path/`, not the default `/admin/`.