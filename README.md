# InstaClone - Production Django Social App

## Project Description

InstaClone is a Django-based social media web application inspired by Instagram. The platform allows users to create accounts, manage profiles, upload posts, interact through likes and comments, follow other users, share stories, exchange direct messages, and receive real-time notifications. The application demonstrates modern web development practices using Django, Channels, WebSockets, and cloud deployment technologies.

## Technologies Used

* Python
* Django 6
* Django Channels
* Daphne
* SQLite (Development)
* PostgreSQL (Production)
* Redis
* Bootstrap 5
* HTML5
* CSS3
* JavaScript
* Cloudinary
* WhiteNoise
* Railway Deployment Platform

## Features

* Django authentication system
* Google OAuth2 login with django-allauth
* User profiles and profile statistics
* Create, edit, and manage posts
* Like and comment system
* Follow and unfollow users
* User search with suggestions
* 24-hour image and video stories
* Story viewer tracking and analytics
* Real-time notifications
* Direct messaging system
* Typing indicators and read receipts
* Online/offline user presence
* Responsive Bootstrap user interface
* Secure production deployment

## Local Setup

```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

Open:

http://127.0.0.1:8000/

## How to Run the Project

1. Clone or download the project.
2. Create and activate a Python virtual environment.
3. Install all required dependencies using requirements.txt.
4. Apply database migrations.
5. Run the Django development server.
6. Access the application through a web browser.

## Deployment Link

Production URL:

https://web-production-beaf7.up.railway.app/

## Team Member Contributions

### Sar Er

* Project planning and system architecture design
* Django backend development
* Database design and implementation
* User authentication and profile management
* Post, Like, Comment, and Follow systems
* Story feature implementation
* Direct Messaging system
* Real-time notifications using Django Channels
* Deployment and server configuration on Railway
* Testing, debugging, and project integration
* Documentation and presentation preparation

### Sarouen Panhasa

* System testing and quality assurance
* Feature validation and user experience feedback
* Documentation review
* Presentation preparation support

### Heng Savin

* User interface testing
* Demonstration preparation
* Project review and evaluation
* Presentation support

## Database Schema

Core relationships:

* User → Profile (One-to-One)
* User → UserStatus (One-to-One)
* User → Posts, Comments, Likes, Follows, Stories, Messages, Notifications (One-to-Many)
* Post → Comments and Likes
* Story → Story Views
* Conversation → Messages
* Notification → Related Posts, Stories, Messages, and Conversations

## Real-Time Architecture

The application uses Django Channels and WebSockets to provide:

* Real-time notifications
* Live messaging
* Typing indicators
* Read receipts
* User online/offline status

WebSocket routes:

* `/ws/notifications/`
* `/ws/chat/<conversation_id>/`
* `/ws/presence/`

## Challenges Faced

* Implementing real-time communication using Django Channels
* Managing WebSocket connections and user presence
* Deploying Django with Daphne on Railway
* Configuring Redis for scalable messaging
* Managing media uploads and cloud storage
* Debugging production deployment issues

## Lessons Learned

* Django project architecture and best practices
* Database relationship design
* Real-time communication with WebSockets
* Cloud deployment and server configuration
* User authentication and security implementation
* Full-stack web application development

## Security Features

* CSRF protection enabled
* Authentication and authorization controls
* Rate limiting for sensitive endpoints
* Secure cookie settings
* HSTS and HTTPS support
* File upload validation
* Production security headers

## Conclusion

InstaClone successfully demonstrates the development of a modern social media platform using Django and related technologies. The project integrates authentication, social interactions, real-time communication, and cloud deployment to provide a complete full-stack web application experience.
