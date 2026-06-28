# DNS and Google OAuth Guide for instaclone.xyz

## DNS records (example)
When Railway gives you DNS targets, create the following records at your domain registrar (example instructions assume Railway asks for CNAME records):

1. Root domain (`instaclone.xyz`)
- If Railway provides an A record or ALIAS/ANAME target, use that. If Railway requires CNAME for `www`, use an ALIAS/ANAME for root.
- Example (if Railway gives an A record):
  - Type: A
  - Name: @
  - Value: <Railway-provided IPv4>

2. WWW (`www.instaclone.xyz`)
- Type: CNAME
- Name: www
- Value: <railway-service-hostname> (e.g., some-service.up.railway.app)

3. Alternatively, follow Railway's domain setup UI — it will show required records.

## Google OAuth setup
1. Go to Google Cloud Console -> APIs & Services -> OAuth consent screen -> configure.
2. Create OAuth 2.0 Client IDs under Credentials.
3. For authorized redirect URIs add:
- `https://instaclone.xyz/accounts/google/login/callback/`
- `https://www.instaclone.xyz/accounts/google/login/callback/`

4. Add `GOOGLE_CLIENT_ID` and `GOOGLE_CLIENT_SECRET` to Railway environment variables.

5. In Django admin -> Sites ensure the `Site` domain is `instaclone.xyz` (or your Railway domain) and `SITE_ID` matches `DJANGO_SITE_ID`.

