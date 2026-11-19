# AutoStock Motors

FastAPI car dealership — public site (vehicle listings, details, applications, test-drive booking, contact) plus a full admin panel (dashboard, vehicles, leads, applications, test drives, contacts, documents, settings).

## Deploy (free, always-on)

[![Deploy to Render](https://render.com/images/deploy-to-render-button.svg)](https://render.com/deploy?repo=https://github.com/workflowsoftware7-svg/autostock-motors)

Or open directly: <https://render.com/deploy?repo=https://github.com/workflowsoftware7-svg/autostock-motors>

After deploy the site is live at `https://autostock-motors.onrender.com`
and the admin panel at `https://autostock-motors.onrender.com/admin/login`.

## Admin login

| | |
|---|---|
| Email | `admin@dealership.com` |
| Password | `lRyNKi1DeWIvlYzVEWkI` |

## Local development

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --host 0.0.0.0 --port 8123
```

## Docker

```bash
docker build -t autostock-motors .
docker run -p 8000:8000 -e PORT=8000 autostock-motors
```

The image ships a pre-seeded SQLite database (11 vehicles with local images), so it is fully populated on first boot.
