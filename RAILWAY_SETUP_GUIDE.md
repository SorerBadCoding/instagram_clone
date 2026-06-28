# Railway Setup Guide for instaclone.xyz

1. Create Railway project
- Go to https://railway.app and create a new project.
- Choose "Deploy from GitHub" and connect your repository.

2. Create Web Service
- Add service -> "Web Service" -> point to your repo and branch.
- Railway will detect a Python app. Ensure `Procfile` is present (it is).

3. Add Postgres
- Add Postgres plugin (Railway Addons -> PostgreSQL).
- Copy the `DATABASE_URL` value and add it to your project's Environment Variables as `DATABASE_URL`.

4. Add Redis (optional, for Channels)
- Add Redis plugin and copy `REDIS_URL` to env vars.

5. Environment variables (add in Railway > Variables)
- `DJANGO_SECRET_KEY` (generate a secure secret)
- `DJANGO_DEBUG=False`
- `DJANGO_ALLOWED_HOSTS=instaclone.xyz,www.instaclone.xyz`
- `DJANGO_SITE_ID=1`
- `DATABASE_URL` (from Postgres addon)
- `REDIS_URL` (from Redis addon if used)
- `GOOGLE_CLIENT_ID` and `GOOGLE_CLIENT_SECRET` (from Google Cloud)

6. Deploy
- Click Deploy. Railway will install `requirements.txt` and use `runtime.txt`.

7. Run migrations & collectstatic
- Open Railway Console -> run these commands:
  ```bash
  python manage.py migrate
  python manage.py collectstatic --noinput
  ```

8. Domain
- Add custom domain in Railway: `instaclone.xyz` and `www.instaclone.xyz`.
- Railway will show DNS records to add at your registrar.

9. Health check
- Configure Railway health check to `https://instaclone.xyz/healthz/`.

10. Verify
- Visit `https://instaclone.xyz/` and test Google Sign In.

