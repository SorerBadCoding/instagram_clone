# Deployment Checklist for instaclone.xyz

Before deploying to Railway, complete these steps:

1. Repo & Railway
- Push your code to a Git remote (GitHub/GitLab).
- Create a Railway project and link the repo.

2. Provision services on Railway
- Add a Postgres service -> copy `DATABASE_URL` to env.
- (Optional) Add a Redis service -> copy `REDIS_URL` to env.

3. Environment variables (Railway project settings)
- `DJANGO_SECRET_KEY` = (generate securely)
- `DJANGO_DEBUG` = `False`
- `DJANGO_ALLOWED_HOSTS` = `instaclone.xyz,www.instaclone.xyz`
- `DATABASE_URL` = (Railway Postgres)
- `REDIS_URL` = (Railway Redis) — optional for Channels
- `GOOGLE_CLIENT_ID` & `GOOGLE_CLIENT_SECRET`
- `DJANGO_SITE_ID` = `1`
- `USE_S3` = `False` (or True if S3 configured)
- If using S3: `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `AWS_STORAGE_BUCKET_NAME`, `AWS_S3_REGION_NAME`

4. Build & start commands
- Railway will use `Procfile` which runs Daphne. Ensure `Procfile` contains:
  ```
  web: daphne -b 0.0.0.0 -p $PORT config.asgi:application
  ```
- `runtime.txt` includes Python version (e.g., `python-3.11.6`).

5. One-off commands (Railway console)
- `python manage.py migrate`
- `python manage.py collectstatic --noinput`
- `python manage.py createsuperuser` (optional)

6. Health check
- Railway health check URL: `https://<your-railway-domain>/healthz/` (should return `{"status":"ok"}`).

7. DNS setup
- Add `instaclone.xyz` and `www.instaclone.xyz` on Railway domains, and create DNS records as Railway instructs (usually CNAME to Railway service).

8. Google OAuth
- Configure OAuth credentials and add redirect uri:
  - `https://instaclone.xyz/accounts/google/login/callback/`

9. Security
- Set `DJANGO_DEBUG=False` and use production `DJANGO_SECRET_KEY`.
- Ensure `DJANGO_SECURE_SSL_REDIRECT=True`.
- Ensure `SESSION_COOKIE_SECURE=True` and `CSRF_COOKIE_SECURE=True`.

10. Media (recommended)
- Use S3 for media. Set `USE_S3=True` and AWS env vars.

11. Monitoring
- Configure logging/monitoring and add alerts for errors.

