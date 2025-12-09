# SocialDistribution - DodgerBlue

A federated social network platform built with Django and Django REST Framework. SocialDistribution allows authors to share posts, follow other authors, and interact across multiple nodes in a distributed network.

See [the project description](https://uofa-cmput404.github.io/general/project.html) for more details.

See [a current live deployment](https://f25-dodgerblue-de6249a319f3.herokuapp.com) of the social distribution!

## Table of Contents

- [Features](#features)
- [Tech Stack](#tech-stack)
- [Setup Instructions](#setup-instructions)
- [Running the Application](#running-the-application)
- [API Documentation](#api-documentation)
- [Project Structure](#project-structure)
- [Testing](#testing)
- [Deployment](#deployment)
- [Contributing](#contributing)
- [License](#license)

## Features

- **User Authentication & Authorization**: Secure user registration and login
- **Author Profiles**: Create and manage author profiles
- **Posts & Entries**: Create, edit, and delete posts with various content types (plain text, markdown, images)
- **Social Features**: Follow/unfollow authors, send follow requests
- **Federated Network**: Connect and interact with other SocialDistribution nodes
- **Likes & Comments**: Engage with posts through likes and comments
- **GitHub Integration**: Sync GitHub activity as posts
- **RESTful API**: Comprehensive API for programmatic access
- **Pagination**: Efficient data browsing with paginated responses

## Tech Stack

- **Backend Framework**: Django 5.2.6
- **API Framework**: Django REST Framework 3.16.1
- **API Documentation**: drf-spectacular (OpenAPI 3.0)
- **Database**: SQLite (development), PostgreSQL (production)
- **Static Files**: WhiteNoise
- **Server**: Gunicorn
- **Task Scheduling**: django-crontab
- **Image Processing**: Pillow

## Setup Instructions

### Prerequisites

- Python 3.8 or higher
- pip (Python package installer)
- virtualenv (recommended)
- Git

### 1. Clone the Repository

```bash
git clone https://github.com/JaxYopek/distributed-social-network.git
cd f25-project-dodgerblue
```

### 2. Create a Virtual Environment

```bash
python -m venv venv
```

### 3. Activate the Virtual Environment

**macOS/Linux:**
```bash
source venv/bin/activate
```

**Windows:**
```bash
venv\Scripts\activate
```

### 4. Install Dependencies

```bash
pip install -r requirements.txt
```

### 5. Navigate to the Django Project Directory

```bash
cd socialdistribution
```

### 6. Run Database Migrations

```bash
python manage.py migrate
```

### 7. Create a Superuser (Admin Account)

```bash
python manage.py createsuperuser
```

Follow the prompts to set up your admin username, email, and password.

### 8. Collect Static Files

```bash
python manage.py collectstatic --noinput
```

## Running the Application

### Development Server

Start the Django development server:

```bash
python manage.py runserver
```

The application will be available at: `http://127.0.0.1:8000/`

### Admin Panel

Access the Django admin panel at: `http://127.0.0.1:8000/admin/`

Log in with the superuser credentials you created earlier.

## API Documentation

The project includes comprehensive API documentation using OpenAPI 3.0 specification.

### Accessing API Documentation

Once the server is running, you can access the API documentation at:

- **Swagger UI**: `http://127.0.0.1:8000/api/schema/swagger-ui/`
  - Interactive API documentation with a modern UI
  - Test API endpoints directly from the browser
  - View request/response schemas

- **ReDoc**: `http://127.0.0.1:8000/api/schema/redoc/`
  - Clean, three-panel documentation layout
  - Better for reading and understanding the API

- **OpenAPI Schema (JSON/YAML)**: `http://127.0.0.1:8000/api/schema/`
  - Raw OpenAPI 3.0 schema
  - Use for importing into API testing tools like Postman or Insomnia

### Main API Endpoints

- `GET /api/authors/` - List all public authors
- `GET /api/authors/{author_fqid}/` - Get author details
- `GET /api/authors/{author_fqid}/posts/` - List author's posts
- `POST /api/authors/{author_fqid}/posts/` - Create a new post
- `GET /api/authors/{author_fqid}/followers/` - List author's followers
- `GET /api/authors/{author_fqid}/inbox/` - Get author's inbox
- `POST /api/authors/{author_fqid}/inbox/` - Send to author's inbox

For a complete list of endpoints, please refer to the Swagger UI documentation.

## Project Structure

```
f25-project-dodgerblue/
├── socialdistribution/          # Main Django project directory
│   ├── manage.py                # Django management script
│   ├── db.sqlite3               # SQLite database (development)
│   ├── schema.yml               # OpenAPI schema definition
│   ├── authors/                 # Authors app (user profiles, follows)
│   │   ├── models.py            # Author, FollowRequest models
│   │   ├── views.py             # Web views
│   │   ├── api_views.py         # API views
│   │   ├── serializers.py       # DRF serializers
│   │   └── tests/               # Unit tests
│   ├── entries/                 # Entries app (posts, comments, likes)
│   │   ├── models.py            # Entry, Comment, RemoteNode models
│   │   ├── views.py             # Web views
│   │   ├── api_views.py         # API views
│   │   ├── serializers.py       # DRF serializers
│   │   └── github_sync.py       # GitHub integration
│   ├── socialdistribution/      # Project settings
│   │   ├── settings.py          # Django settings
│   │   ├── urls.py              # URL configuration
│   │   ├── authentication.py    # Custom authentication
│   │   └── permissions.py       # Custom permissions
│   ├── static/                  # Static files (CSS, JS)
│   ├── templates/               # HTML templates
│   └── media/                   # User-uploaded files
├── requirements.txt             # Python dependencies
├── Procfile                     # Heroku deployment configuration
└── README.md                    # This file
```

## Testing

### Run All Tests

```bash
python manage.py test
```

### Run Tests for Specific Apps

```bash
python manage.py test authors
python manage.py test entries
```

### Run Specific Test Classes or Methods

```bash
python manage.py test authors.tests.test_models.AuthorModelTest
python manage.py test authors.tests.test_models.AuthorModelTest.test_author_creation
```

## Deployment

The application is configured for deployment on Heroku using the included `Procfile`.

### Environment Variables

For production deployment, set the following environment variables:

- `DEBUG=0` - Disable debug mode
- `SECRET_KEY` - Django secret key (generate a new one for production)
- `DATABASE_URL` - PostgreSQL database URL
- `ALLOWED_HOSTS` - Comma-separated list of allowed hosts

### Deploy to Heroku

```bash
heroku create your-app-name
heroku addons:create heroku-postgresql:mini
git push heroku main
heroku run python socialdistribution/manage.py migrate
heroku run python socialdistribution/manage.py createsuperuser
```

## Contributing

This is a university course project. Contributions are limited to team members.

### Team DodgerBlue Members
- Jax Yopek
- Jordan Brent
- Titobiloluwa Adeniji
- Zhikun Liu
- Botsian Liu
- Syed Shahmeer Rahman

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

**Course**: CMPUT404 - Web Applications and Architecture  
**University**: University of Alberta  
**Semester**: Fall 2025
