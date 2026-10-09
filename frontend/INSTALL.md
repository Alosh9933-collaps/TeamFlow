# TeamFlow Frontend setup

This pack replaces the current `src/` application code and updates `vite.config.ts`. It intentionally does not replace your existing `package.json` or TypeScript config.

## 1. Copy files

Copy the contents of this pack into your existing `frontend/` folder, merging folders and replacing files with the same path. In particular, replace `src/` and `vite.config.ts`.

## 2. Install the Tailwind Vite plugin

Open a terminal in `frontend/` and run:

```powershell
npm install tailwindcss @tailwindcss/vite
```

`axios` and `react-router-dom` should already be installed from the previous steps. If not:

```powershell
npm install axios react-router-dom
```

## 3. Run the frontend

```powershell
npm run dev
```

The Vite config pins the host to `127.0.0.1` to avoid the IPv6 localhost issue experienced during setup. Open the URL Vite prints, usually `http://127.0.0.1:5173/`.

## 4. Run Django in a separate terminal

From the `TeamFlow/` backend folder, with the Python virtual environment activated:

```powershell
python manage.py runserver
```

The API base URL defaults to `http://127.0.0.1:8000/api/`. You may copy `.env.example` to `.env.local` if you need to change it; Vite reads `VITE_API_BASE_URL`.

## Known backend URL assumptions

The app uses the already tested paths `auth/token/`, `auth/me/`, `teams/`, `projects/`, and `tasks/`. It assumes `auth/register/` for registration, `notifications/<id>/read/`, `notifications/read-all/`, and `projects/<id>/activity/` for ancillary features. If one of those differs in Django `urls.py`, change the corresponding constant in `src/services/endpoints.ts`—do not hunt through the pages.

The registration payload assumes `username`, `email`, `password`, and `password_confirm`. If `RegisterSerializer` uses another confirmation-field name or requires different fields, adjust the payload in `src/context/AuthContext.tsx` or the register form.

## Notes

- JWT access and refresh tokens are kept in `localStorage` for this portfolio/demo frontend. This is straightforward for local development; production token storage should be revisited for the deployment's threat model.
- The backend must allow the exact frontend origin in `CORS_ALLOWED_ORIGINS`. Because the Vite host is pinned to IPv4, the expected origin is `http://127.0.0.1:5173`.
- A task is sent with `project`, `title`, `description`, `priority`, `due_date`, and an empty `tags` list to match the task API tests discussed earlier.
