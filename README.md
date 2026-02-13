 # Checkin — Django-based check-in / check-out system

Light-weight Django application for site check-in/check-out workflows (staff, visitors, contractors, associated staff), with a manager UI and public QR/scan portals. Uses SB Admin 2 frontend assets and Django apps `access` and `core` for core functionality.

**Key features**
- Visitor / contractor / staff sign-in and checkout flows
- Token-based public scan pages and QR code endpoints
- Manager dashboard for site and staff administration
- Custom `AUTH_USER_MODEL` and site-scoped managers

**Repository layout (selected)**
- `manage.py` — Django management entrypoint
- `config/` — Django settings, URLs, WSGI/ASGI
- `access/` — access control app (models, views, migrations)
- `core/` — site and user core models, utilities
- `templates/`, `static/`, `staticfiles/` — UI templates and assets
- `db.sqlite3` — development SQLite DB (included for demo)

## Quickstart (development)
Recommended: use a virtual environment and Python 3.10+ (project was developed on a newer Python).

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

python manage.py migrate
python manage.py createsuperuser
python manage.py runserver 0.0.0.0:8000
```

Open `http://127.0.0.1:8000/` and visit `/admin/` to configure initial data.

## Important URLs
- Admin: `/admin/`
- Manager UI (after login): `/manager/`
- Public scan/QR page: `/s/<token>/`

## Configuration & environment
- See `config/settings.py` for current defaults (DEBUG=True, SQLite). For production, set the following environment variables or override settings:
  - `SECRET_KEY` — set a secure secret
  - `DEBUG=False` — disable debug in production
  - `ALLOWED_HOSTS` — configure accordingly
  - Database settings — replace SQLite with Postgres/MySQL for production

Run `python manage.py collectstatic` before serving static files in production. `config/wsgi.py` and `config/asgi.py` are provided for WSGI/ASGI deployments.

## Database & migrations
- The repo contains migration history under `access/migrations/` and `core/migrations/`.
- A development `db.sqlite3` is included for convenience; we recommend removing it from source control for production (see `.gitignore`).

## Deployment (basic guidance)
1. Pin exact dependency versions and install them in a clean environment.
2. Use a production WSGI server (e.g., Gunicorn) and a reverse proxy (e.g., Nginx).
3. Set environment variables (`SECRET_KEY`, `DEBUG=False`, `DATABASE_URL` or configure `DATABASES`), migrate, and run `collectstatic`.

Example Gunicorn run (from project root):
```bash
gunicorn config.wsgi:application --bind 0.0.0.0:8000 --workers 3
```

## Contributing
- Please open issues or pull requests. Include tests and follow the repository style.

## Security
- Do not commit secrets into source. Use environment variables or a secrets manager for production credentials.

## Notes
- `requirements.txt` contains third-party libs; Django is intentionally pinned to a 5.x range in repository updates.
- If you want me to also add `CONTRIBUTING.md` and `CODE_OF_CONDUCT.md`, say so and I'll add concise templates.

---
Updated: February 13, 2026
