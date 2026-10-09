# TeamFlow

TeamFlow is a full-stack team and project management application. It combines a Django REST Framework API with a React + TypeScript frontend, PostgreSQL persistence, JWT authentication, role-based permissions, activity tracking, and notifications.

## Features

- User registration and JWT-based authentication
- Team creation and team membership management
- Project creation and project join-request workflows
- Task management with role-aware access control
- Activity logs and in-app notifications
- REST API built with Django REST Framework
- OpenAPI schema generation with `drf-spectacular`
- React + TypeScript single-page frontend
- PostgreSQL development database via Docker Compose

## Tech stack

**Backend:** Python, Django, Django REST Framework, Simple JWT, django-filter, drf-spectacular
**Frontend:** React, TypeScript, Vite, Axios, React Router
**Database:** PostgreSQL
**Development / tooling:** Docker Compose, Git, GitHub Actions (CI setup planned)

## Project structure

```text
TeamFlow/
├── apps/
│   ├── accounts/
│   ├── activity/
│   ├── notifications/
│   ├── projects/
│   ├── tasks/
│   └── teams/
├── config/                 # Django settings and URL configuration
├── frontend/               # React + TypeScript application
├── docker-compose.yml      # PostgreSQL development service
├── requirements.txt        # Python dependencies
├── schema.yml              # Generated OpenAPI schema
└── manage.py
```

## Requirements

- Python 3.12 or newer
- Node.js and npm
- Docker Desktop with Docker Compose

The commands below use Windows PowerShell. Run backend and frontend commands in separate terminal windows when both servers need to stay running.

## Local setup

### 1. Clone the repository

```powershell
git clone https://github.com/Alosh9933-collaps/TeamFlow.git
cd TeamFlow
```

### 2. Create the Python environment

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### 3. Configure environment variables

Create your local `.env` file from the example:

```powershell
Copy-Item .env.example .env
```

Edit `.env` and fill in local development values. For example:

```dotenv
SECRET_KEY=replace-with-a-locally-generated-secret
DEBUG=True
ALLOWED_HOSTS=127.0.0.1,localhost

DB_NAME=teamflow
DB_USER=teamflow
DB_PASSWORD=replace-with-a-local-database-password
DB_HOST=127.0.0.1
DB_PORT=5433
```

Use the same database name, username, and password expected by `docker-compose.yml`. Do not commit `.env` or put real secrets in `.env.example`.

### 4. Start PostgreSQL and prepare Django

```powershell
docker compose up -d
python manage.py migrate
```

Optional: create an administrator account for Django Admin:

```powershell
python manage.py createsuperuser
```

### 5. Run the backend

```powershell
python manage.py runserver 127.0.0.1:8000
```

The backend API is served at `http://127.0.0.1:8000/`. The JWT token endpoint is `http://127.0.0.1:8000/api/auth/token/`.

### 6. Run the frontend

Open a second PowerShell window and run:

```powershell
Copy-Item frontend/.env.example frontend/.env
cd frontend
npm ci
npm run dev -- --host 127.0.0.1
```

Open `http://127.0.0.1:5173/` in your browser. The frontend API base URL is configured with `VITE_API_BASE_URL` in `frontend/.env`.

## Tests and API schema

Run the Django test suite from the repository root with the virtual environment activated:

```powershell
python manage.py test
```

Validate and regenerate the OpenAPI schema with:

```powershell
python manage.py spectacular --file schema.yml --validate
```

Build the frontend for production with:

```powershell
cd frontend
npm ci
npm run build
```

## Environment and security notes

- `.env` files, Python virtual environments, `node_modules`, and build output are excluded by `.gitignore`.
- The `.env.example` files contain configuration templates only; replace placeholders in your own local `.env` files.
- Before production deployment, configure a strong secret key, `DEBUG=False`, production `ALLOWED_HOSTS`, secure HTTPS settings, and production-grade database credentials.

## Current project status

The backend modules, frontend pages, authentication flow, API integration, and automated backend tests have been developed and tested locally. Production deployment and continuous integration are separate follow-up steps.
