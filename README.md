# AutoStock Motors

FastAPI car dealership — public site (vehicle listings, details, applications, test-drive booking, contact) plus a full admin panel (dashboard, vehicles, leads, applications, test drives, contacts, documents, settings).

## Deploy (free)

[![Deploy to Render](https://render.com/images/deploy-to-render-button.svg)](https://render.com/deploy?repo=https://github.com/codeflare-tech/autostock-motors)

Or open directly: <https://render.com/deploy?repo=https://github.com/codeflare-tech/autostock-motors>

## Admin login

| | |
|---|---|
| Email | `admin@dealership.com` |
| Password | Set the `ADMIN_PASSWORD` environment variable before the first boot. If it is unset, a fallback is generated and printed in the startup log. |

The seeded database ships with an admin account; change the password from the admin panel after logging in.

## Local development

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --host 0.0.0.0 --port 8123
```

## Docker

```bash
docker build -t autostock-motors .
docker run -p 8000:8000 -e PORT=8000 -e ADMIN_PASSWORD=change-me autostock-motors
```

The image ships a pre-seeded SQLite database (11 vehicles with local images), so it is fully populated on first boot.

## Configuration

| Variable | Purpose |
|---|---|
| `ADMIN_EMAIL` | Admin login email (default `admin@dealership.com`) |
| `ADMIN_PASSWORD` | Admin login password |
| `DATABASE_URL` | Optional managed database (Postgres/MySQL) for persistent data |
| `PORT` | HTTP port (Render injects this) |
