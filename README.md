# InstaClone - Production Django Social App

A Django Instagram-style social platform with the existing Bootstrap UI preserved and a restored production-ready backend.

## Features

- Django auth plus Google OAuth2 with django-allauth
- Automatic profile/status creation for every user
- Posts, likes, comments, follows, profile stats, followers/following lists
- 24-hour image/video stories with privacy, viewer tracking, and owner analytics
- Real-time notifications for follows, likes, comments, messages, and story views
- Direct messages with one-to-one conversations, WebSockets, typing indicators, read receipts, image upload fallback, timestamps, and older-message endpoint
- User search by username, name, and bio with AJAX suggestions, recent searches, and suggested users
- Online/offline presence through Django Channels
- SQLite locally, PostgreSQL through DATABASE_URL in production
- Daphne ASGI, WhiteNoise static files, secure production settings, and deployment-ready environment variables

## Local Setup

```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

Open http://127.0.0.1:8000/.

The existing migration seeds a local superuser:

```text
username: potling
password: Potling123!
```

## Google OAuth2 Setup

1. Create OAuth credentials in Google Cloud Console.
2. Add redirect URI: `http://127.0.0.1:8000/accounts/google/login/callback/` for local development.
3. Set env vars:

```env
GOOGLE_CLIENT_ID=your-client-id
GOOGLE_CLIENT_SECRET=your-client-secret
```

Optional Cloudinary storage for Railway production:

```env
USE_CLOUDINARY=True
CLOUDINARY_URL=cloudinary://API_KEY:API_SECRET@CLOUD_NAME
```

Allauth auto-registers new users and the app stores Google ID, email/name fields, and avatar URL on the linked profile.

## Environment Variables

Copy `.env.example` into your platform/environment manager and set:

```env
DJANGO_SECRET_KEY=change-me
DJANGO_DEBUG=False
DJANGO_ALLOWED_HOSTS=your-domain.com,www.your-domain.com
DJANGO_CSRF_TRUSTED_ORIGINS=https://your-domain.com,https://www.your-domain.com
DATABASE_URL=postgresql://USER:PASSWORD@HOST:5432/DBNAME
REDIS_URL=redis://HOST:6379/0
GOOGLE_CLIENT_ID=...
GOOGLE_CLIENT_SECRET=...
```

`REDIS_URL` is optional locally. In production, use Redis for WebSocket fan-out when running more than one process.

## Deployment

### Render or Railway

- Build command: `pip install -r requirements.txt && python manage.py collectstatic --noinput && python manage.py migrate`
- Start command: `daphne -b 0.0.0.0 -p $PORT config.asgi:application`
- Add PostgreSQL and Redis services.
- Set all env vars from `.env.example`.

### Ubuntu/VPS/aaPanel

```bash
git clone <repo>
cd instagram_clone
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python manage.py collectstatic --noinput
python manage.py migrate
daphne -b 0.0.0.0 -p 8000 config.asgi:application
```

Put Nginx in front for HTTPS, static files, media files, and WebSocket proxying. Proxy `/ws/` with HTTP/1.1 upgrade headers.

## Database Schema

Core relationships:

- User 1-1 Profile
- User 1-1 UserStatus
- User 1-N Post, Comment, Like, Follow, Story, Message, Notification
- Post 1-N Comment, Like, Notification
- Story 1-N StoryView and Notification
- Conversation M-N User through participants
- Conversation 1-N Message
- Notification optionally points to Post, Story, Message, or Conversation
- RecentSearch connects a searching user to a searched user

Important constraints and indexes:

- Unique like per user/post
- Unique follow per follower/following with self-follow check
- Unique story view per story/viewer
- Unique recent search per user/searched user
- Indexed feeds, comments, follows, notifications, story expiry, messages, and presence fields

## Real-Time Architecture

Channels routes:

- `/ws/notifications/` pushes notification payloads to the authenticated user
- `/ws/chat/<conversation_id>/` handles text messages, typing, and read receipts
- `/ws/presence/` updates online/offline state

Image messages use normal multipart POST upload for file safety; text messages use WebSockets.

## Security Notes

- CSRF middleware remains enabled for all forms
- Auth and authorization checks protect owner-only and participant-only routes
- Upload forms validate size and MIME type
- Rate limiting wraps high-volume like/comment/follow endpoints
- Production cookies, HSTS, X-Frame-Options, content-type sniffing protection, and proxy SSL settings are enabled when `DJANGO_DEBUG=False`
