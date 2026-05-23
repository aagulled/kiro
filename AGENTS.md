# Kirokiro Property Listing Platform - Agent Guide

## Essential Commands

**Start development server:**
```bash
python manage.py runserver
```

**Run tests:**
```bash
# Run all tests
pytest

# Run tests for specific app
pytest apps/core/

# Run tests with coverage
pytest --cov=apps
```

**Database operations:**
```bash
# Create migrations after model changes
python manage.py makemigrations

# Apply migrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser
```

**Code quality:**
```bash
# Format code
black .

# Import sorting
isort .

# Linting
flake8 .

# Type checking
mypy .
```

## Project Structure

<<<<<<< HEAD
- **Settings:** `kirokiro/settings.py` (environment via `.env`)
=======
- **Settings:** `kirokiro/settings.py` (environment variables)
>>>>>>> e13cee5 (update)
- **URLs:** `kirokiro/urls.py`
- **Apps:** `/apps/` directory contains all feature apps
- **Custom User Model:** `kiro.User` (defined in kiro app)
- **Static files:** Collected to `staticfiles/`
- **Media files:** Stored in `media/`
- **Logs:** `logs/kirokiro.log` and `logs/security.log`

## Key Features

- **API:** Django REST Framework with JWT authentication
- **Multi-tenancy:** django-tenants configured but disabled in settings (commented out)
- **Caching:** Configured for different apps (locmem backend)
- **Internationalization:** Supports multiple languages (en, es, fr, de, ar, so)
- **File Uploads:** Limited to 5MB, JPEG/PNG/WebP images only
- **Rate Limiting:** Configured via Django REST Framework throttling

## Environment

<<<<<<< HEAD
- Copy `.env.example` to `.env` and configure:
  - `SECRET_KEY` (required)
  - `DEBUG` (bool)
  - `ALLOWED_HOSTS` (list)
  - Database URL (via `env.db_url()`)
=======
Activate the `kiro` environment and set variables (or `source kirokiro/kiro`):
  - `SECRET_KEY` (required)
  - `DEBUG` (bool)
  - `ALLOWED_HOSTS` (list)
  - `DATABASE_URL` (PostgreSQL, e.g. postgres://user:pass@localhost:5432/kirokiro)
>>>>>>> e13cee5 (update)
  - Email settings
  - JWT token lifetimes

## Testing Notes

- Uses `pytest` with `pytest-django` plugin
- Factories: `factory_boy`
- Test data generation: `Faker`
- Custom exception handler: `apps.core.exceptions.custom_exception_handler`

## Important Constraints

1. Multi-tenancy settings are currently commented out in settings.py
2. Custom user model is `kiro.User`, not Django's default
3. API defaults to `AllowAny` permission (override in views as needed)
4. Static files served by WhiteNoise in production