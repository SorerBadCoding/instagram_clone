# Deployment Guide — Railway

This guide describes deploying the Instagram Clone to Railway.

Prerequisites
- A Railway account and a connected Git repository (this repo).
- Railway Postgres addon and Railway Redis addon (optional, for Channels).

Steps
1. Create a new Railway project and link your Git repository.
2. Add a new "Service" -> "Web Service" and point to your repo/branch.
   - Railway recognizes `Procfile` and will use the `web` command. Your `Procfile` contains:
     ```
     web: daphne -b 0.0.0.0 -p $PORT config.asgi:application
     ```
3. Add environment variables in Railway Project Settings (see `.env.example`). Required vars:
   - `DJANGO_SECRET_KEY` — generate a secure value.
   - `DJANGO_DEBUG=False`
   - `DJANGO_ALLOWED_HOSTS=instaclone.xyz,www.instaclone.xyz`
   - `DATABASE_URL` — provided by the Postgres addon.
   - `REDIS_URL` — provided by the Redis addon if you enable Channels.
   - `GOOGLE_CLIENT_ID` and `GOOGLE_CLIENT_SECRET` for Google OAuth.
   - `DJANGO_SITE_ID=1`
4. Add a Postgres addon (Railway) and copy `DATABASE_URL` into env.
5. (Optional) Add a Redis addon and copy `REDIS_URL` into env.
6. Deploy — Railway will install `requirements.txt` and run build.
7. Run one‑off commands via Railway console (or 'Run' -> "New Job"):
   ```bash
   python manage.py migrate
   python manage.py collectstatic --noinput
   ```
8. Configure a custom domain in Railway (add `instaclone.xyz` and `www.instaclone.xyz`) and follow Railway's DNS instructions.
9. Add Google OAuth redirect URI in Google Console: `https://instaclone.xyz/accounts/google/login/callback/`

Notes
- Railway provides ephemeral filesystem; use S3 for media in production (set `USE_S3=True` and provide AWS env vars).
- Keep `DEBUG=False` and set secure cookie/HSTS settings as in `.env.example`.

Healthcheck endpoint
- The project exposes `GET /healthz/` which returns `{"status":"ok"}`.

If you want, I can:
- Add `django-storages` + S3 config and update `requirements.txt`.
- Create Railway-specific scripts or `.railway` config.
