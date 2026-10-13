# TeamFlow

[![CI](https://github.com/Alosh9933-collaps/TeamFlow/actions/workflows/ci.yml/badge.svg)](https://github.com/Alosh9933-collaps/TeamFlow/actions/workflows/ci.yml)

**TeamFlow** is a full-stack team and project management application built with Django REST Framework, React, TypeScript, and PostgreSQL. It provides JWT authentication, role-based access control, team and project membership management, task tracking, activity logs, and notifications.

## Live Application

- **Frontend:** https://teamflow-frontend-3kgv.onrender.com/
- **Backend:** https://teamflow-api-alosh9933.onrender.com/
- **Repository:** https://github.com/Alosh9933-collaps/TeamFlow

The frontend and backend are deployed on Render, with PostgreSQL hosted on Neon.

## Features

### Authentication and Accounts

- User registration and JWT-based authentication.
- Email verification for newly registered accounts.
- Password reset through email.
- Protected API endpoints.

### Teams and Projects

- Create and manage teams.
- Manage team membership and roles.
- Create projects within teams.
- Manage project membership.
- Support project join-request workflows.
- Restrict access according to team and project permissions.

### Tasks and Collaboration

- Create, update, and manage project tasks.
- Apply role-aware access control to task operations.
- Record activity logs for relevant actions.
- Provide in-app notifications.

### API and Quality

- REST API built with Django REST Framework.
- JWT authentication using Simple JWT.
- API schema generation and validation with `drf-spectacular`.
- Automated Django tests.
- Automated frontend production builds through GitHub Actions.

## Technology Stack

| Area | Technologies |
|---|---|
| Backend | Python, Django, Django REST Framework |
| Authentication | Simple JWT |
| API documentation | drf-spectacular, OpenAPI |
| Filtering | django-filter |
| Database | PostgreSQL |
| Frontend | React, TypeScript, Vite |
| API integration | Axios |
| Routing | React Router |
| Static files | WhiteNoise |
| Email delivery | SendGrid API |
| Development database | Docker Compose |
| Deployment | Render, Neon |
| CI | GitHub Actions |

## Project Structure

```text
TeamFlow/
├── apps/
│   ├── accounts/        # User accounts and authentication
│   ├── activity/        # Activity log functionality
│   ├── notifications/   # In-app notifications
│   ├── projects/        # Projects and project membership
│   ├── tasks/           # Task management
│   └── teams/           # Teams and team membership
├── config/              # Django settings, URLs, and WSGI
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   ├── context/
│   │   ├── lib/
│   │   ├── pages/
│   │   ├── services/
│   │   └── types/
│   ├── package.json
│   └── vite.config.ts
├── .github/
│   └── workflows/
│       └── ci.yml       # Continuous integration workflow
├── docker-compose.yml
├── requirements.txt
├── schema.yml           # Generated OpenAPI schema
└── manage.py
```

## Requirements

- Python 3.14 (used in the current CI configuration)
- Node.js 24 and npm
- Docker Desktop with Docker Compose
- Git

The setup commands below use Windows PowerShell.

## Local Development

### 1. Clone the repository

```powershell
git clone https://github.com/Alosh9933-collaps/TeamFlow.git
cd TeamFlow
```

### 2. Create and activate the Python environment

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### 3. Configure environment variables

Create your local environment file:

```powershell
Copy-Item .env.example .env
```

Edit `.env` and configure local development values. For example:

```dotenv
SECRET_KEY=replace-with-a-strong-local-secret
DEBUG=True
ALLOWED_HOSTS=127.0.0.1,localhost

DB_NAME=teamflow
DB_USER=teamflow
DB_PASSWORD=replace-with-a-local-database-password
DB_HOST=127.0.0.1
DB_PORT=5433
DB_SSLMODE=prefer

FRONTEND_URL=http://127.0.0.1:5173
EMAIL_PROVIDER=console
SENDGRID_API_KEY=
DEFAULT_FROM_EMAIL=
```

Use values compatible with the database configuration in `docker-compose.yml`. Keep real credentials and API keys in your local `.env` file or deployment environment variables. Never commit secrets.

### 4. Start PostgreSQL and apply migrations

```powershell
docker compose up -d
python manage.py migrate
```

Optionally, create an administrator for Django Admin:

```powershell
python manage.py createsuperuser
```

### 5. Start the backend

From the repository root:

```powershell
python manage.py runserver 127.0.0.1:8000
```

The local API is available at:

`http://127.0.0.1:8000/`

The JWT token endpoint is:

`http://127.0.0.1:8000/api/auth/token/`

### 6. Start the frontend

Open a second PowerShell terminal. From the repository root, configure the frontend environment and start Vite:

```powershell
Copy-Item frontend/.env.example frontend/.env
cd frontend
npm ci
npm run dev -- --host 127.0.0.1
```

Open:

`http://127.0.0.1:5173/`

The frontend API URL is configured through `VITE_API_BASE_URL` in `frontend/.env`.

## Tests and API Schema

### Run Django tests

From the repository root with the Python environment activated:

```powershell
python manage.py check
python manage.py test
```

### Generate and validate the OpenAPI schema

```powershell
python manage.py spectacular --file schema.yml --validate
```

### Build the frontend

From the frontend directory:

```powershell
npm ci
npm run build
```

## Continuous Integration

The GitHub Actions workflow in `.github/workflows/ci.yml` runs automatically on pushes and pull requests targeting `main`.

It includes two jobs:

- **Backend Tests:** prepares PostgreSQL, installs Python dependencies, checks Django configuration, and runs the Django test suite.
- **Frontend Build:** installs Node.js dependencies and builds the React application.

The CI badge at the top of this README links to the workflow results.

## Deployment

The production application uses:

- **Render** for the Django backend.
- **Render Static Site** for the React frontend.
- **Neon** for PostgreSQL.
- **SendGrid API** for transactional email.

Production configuration is supplied through environment variables rather than committed credentials.

Important production settings include:

- `SECRET_KEY`
- `DEBUG=False`
- `ALLOWED_HOSTS`
- `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_HOST`, and `DB_PORT`
- `DB_SSLMODE=require`
- `FRONTEND_URL`
- `CORS_ALLOWED_ORIGINS`
- `EMAIL_PROVIDER`
- `SENDGRID_API_KEY`
- `DEFAULT_FROM_EMAIL`

Do not put production credentials in source files or commit them to GitHub.

## Security

- Authentication is handled through JWTs.
- API permissions enforce role-aware access to teams, projects, and tasks.
- Access to other users' projects and tasks is restricted by backend authorization.
- Production uses HTTPS-related Django security settings.
- Secrets are configured through environment variables.
- Automated tests help prevent authorization regressions.

## Project Status

TeamFlow is deployed and accessible online. The project includes a Django REST API, a React frontend, a PostgreSQL database, email-based account workflows, role-aware permissions, automated backend tests, and a GitHub Actions CI workflow.

The project is intended as a portfolio demonstration of backend API development, relational database integration, authentication, authorization, automated testing, and deployment.