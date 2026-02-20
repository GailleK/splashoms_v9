# Railway Deploy Guide

## Services

1. `oms_django` (backend API)
- Root directory: `oms_django`
- Config file: `oms_django/railway.json`
- Exposes: `/api/...`

2. `oms_vue` (frontend)
- Root directory: `oms_vue`
- Config file: `oms_vue/railway.json`

## Backend Env Vars

- `DEBUG=False`
- `SECRET_KEY=<long-random-secret>`
- `ALLOWED_HOSTS=<your-backend-domain>`
- `DATABASE_URL=<Railway Postgres URL>`
- `CORS_ALLOWED_ORIGINS=<your-frontend-domain>`
- `CSRF_TRUSTED_ORIGINS=<your-frontend-domain>`
- optional: `SECURE_SSL_REDIRECT=True`
- optional: `SECURE_HSTS_SECONDS=31536000`

## Frontend Env Vars

- `VITE_API_BASE_URL=https://<your-backend-domain>/api`

## Notes

- Backend pre-deploy runs migrations + collectstatic.
- Backend health endpoint: `/healthz/`.
- JWT auth endpoints are under `/api/auth/`.
- If backend domain changes, update both CORS/CSRF and frontend `VITE_API_BASE_URL`.
