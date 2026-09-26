"""
Django settings for fuel_route_api project.
Simple settings file - this is a small assessment project, so kept minimal.
"""
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

# NOTE: In a real production project this would come from an environment
# variable. For an assessment project, a hardcoded dev key is fine.
SECRET_KEY = 'django-insecure-change-this-key-for-assessment-only'

DEBUG = True

ALLOWED_HOSTS = ['*']

INSTALLED_APPS = [
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.staticfiles',
    'rest_framework',
    'planner',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.middleware.common.CommonMiddleware',
]

ROOT_URLCONF = 'fuel_route_api.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
            ],
        },
    },
]

WSGI_APPLICATION = 'fuel_route_api.wsgi.application'

# We don't need a database for this project (no models, no user auth) -
# but Django wants SOME database configured, so we use SQLite (does not
# even need to exist/be migrated for this project to run).
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

STATIC_URL = 'static/'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
