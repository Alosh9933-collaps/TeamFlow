# TeamFlow password-reset patch

This patch adds the missing React password recovery pages and fixes the Django reset email URL.

## Files included

Copy these files over the same paths in your TeamFlow project:
- `frontend/src/App.tsx`
- `frontend/src/pages/LoginPage.tsx`
- `frontend/src/pages/ForgotPasswordPage.tsx` (new)
- `frontend/src/pages/ResetPasswordPage.tsx` (new)
- `frontend/src/services/endpoints.ts`
- `apps/accounts/views.py`

The `.env.example` here includes the safe placeholders from your current example plus `FRONTEND_URL`. It is only an example; **do not overwrite your real `.env`**.

## Required Django setting

In `config/settings.py`, add this near the other environment-based settings (your project already loads `.env`):

```python
FRONTEND_URL = os.getenv(
    "FRONTEND_URL",
    "http://127.0.0.1:5173",
).rstrip("/")
```

If `os` is not already imported at the top, add `import os`. It should already be present based on your current database setup.

For local use, add this line to your ignored `.env`:
`FRONTEND_URL=http://127.0.0.1:5173`

For production, set `FRONTEND_URL` in the Backend hosting provider's environment variables to the exact public frontend base URL, for example `https://your-frontend.example.com` (without a trailing slash).

## How the flow works

1. Login page links to `/forgot-password`.
2. The forgot-password page posts `{ "email": "..." }` to `auth/password-reset/`.
3. Django sends a reset email with a link to `/reset-password/<uidb64>/<token>` on the React frontend.
4. The React reset page posts `{ "password": "...", "password_confirm": "..." }` to `auth/password-reset/<uidb64>/<token>/`.
5. The existing Django password validation and token logic remains in place.

The response after requesting a reset is intentionally generic so the UI does not reveal whether an email belongs to an account.

## Test locally

Run the Django backend as usual. In another terminal:
```powershell
cd frontend
npm run dev -- --host 127.0.0.1
```

Then:
- Open `http://127.0.0.1:5173/login`.
- Click **Forgot password?**.
- Submit the account email.
- In development, retrieve the email using your configured Django email backend. If it prints messages to the console, open the reset link from the terminal output.
- Set a new password, then confirm you can sign in with it.

If the reset email URL is not visible in local development, inspect `send_password_reset_email` in `apps/accounts/services.py` and the configured `EMAIL_BACKEND`; do not print secrets to logs.

## Validation before committing

From the project root:
```powershell
python manage.py check
python manage.py test
cd frontend
npm run build
```

Commit and push only after all checks pass.
