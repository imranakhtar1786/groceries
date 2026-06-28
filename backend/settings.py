"""
Django settings for backend project.
"""

import os
from pathlib import Path
import dj_database_url
from dotenv import load_dotenv

load_dotenv()


BASE_DIR = Path(__file__).resolve().parent.parent


# SECURITY
SECRET_KEY = os.environ.get(
    "SECRET_KEY",
    "django-insecure-change-this"
)

DEBUG = os.environ.get("DEBUG", "True") == "True"

ALLOWED_HOSTS = ["*"]

CORS_ALLOW_ALL_ORIGINS = True


# APPLICATIONS

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",

    "rest_framework",
    "corsheaders",
    "django_filters",
    "storages",

    "users",
    "locations",
    "products",
    "orders",
    "promotions",
]


MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",

    "corsheaders.middleware.CorsMiddleware",

    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",

    "django.middleware.csrf.CsrfViewMiddleware",

    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",

    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]


ROOT_URLCONF = "backend.urls"


TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],

        "APP_DIRS": True,

        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",

                "django.contrib.auth.context_processors.auth",

                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]


WSGI_APPLICATION = "backend.wsgi.application"



# DATABASE - SUPABASE POSTGRESQL


DATABASE_URL = os.environ.get("DATABASE_URL")

if not DATABASE_URL:
    raise ValueError(
        "DATABASE_URL is missing in .env"
    )


DATABASES = {
    "default": dj_database_url.parse(
        DATABASE_URL,
        conn_max_age=600,
        ssl_require=True
    )
}



# PASSWORD VALIDATION


AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME":
        "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },

    {
        "NAME":
        "django.contrib.auth.password_validation.MinimumLengthValidator",
    },

    {
        "NAME":
        "django.contrib.auth.password_validation.CommonPasswordValidator",
    },

    {
        "NAME":
        "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]



# LANGUAGE


LANGUAGE_CODE = "en-us"

TIME_ZONE = "UTC"

USE_I18N = True

USE_TZ = True



# STATIC FILES


STATIC_URL = "/static/"

STATIC_ROOT = BASE_DIR / "staticfiles"



# SUPABASE CONFIG


SUPABASE_URL = os.environ.get(
    "SUPABASE_URL"
)

SUPABASE_PUBLISHABLE_KEY = os.environ.get(
    "SUPABASE_PUBLISHABLE_KEY"
)

SUPABASE_SECRET_KEY = os.environ.get(
    "SUPABASE_SECRET_KEY"
)



# SUPABASE STORAGE (S3)


# SUPABASE STORAGE (S3 COMPATIBLE)

AWS_ACCESS_KEY_ID = os.environ.get("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.environ.get("AWS_SECRET_ACCESS_KEY")

AWS_STORAGE_BUCKET_NAME = os.environ.get("AWS_STORAGE_BUCKET_NAME", "groceries")

AWS_S3_ENDPOINT_URL = "https://qhtskxffjwyqjrthgvla.storage.supabase.co/storage/v1/s3"

AWS_S3_REGION_NAME = "ap-northeast-1"

AWS_S3_SIGNATURE_VERSION = "s3v4"

AWS_S3_ADDRESSING_STYLE = "path"

AWS_QUERYSTRING_AUTH = False


# Django 5.2 storage config

STORAGES = {

    "default": {

        "BACKEND":
        "storages.backends.s3boto3.S3Boto3Storage",

    },


    "staticfiles": {

        "BACKEND":
        "whitenoise.storage.CompressedManifestStaticFilesStorage",

    },

}



# UPSTASH REDIS CACHE


UPSTASH_REDIS_REST_URL = os.environ.get(
    "UPSTASH_REDIS_REST_URL"
)


UPSTASH_REDIS_REST_TOKEN = os.environ.get(
    "UPSTASH_REDIS_REST_TOKEN"
)



if UPSTASH_REDIS_REST_URL and UPSTASH_REDIS_REST_TOKEN:

    CACHES = {

        "default": {

            "BACKEND":
            "backend.upstash_cache.UpstashRESTCache",


            "LOCATION":
            UPSTASH_REDIS_REST_URL,

        }

    }


else:


    CACHES = {

        "default": {

            "BACKEND":
            "django.core.cache.backends.locmem.LocMemCache",

        }

    }



# DEFAULT PRIMARY KEY


DEFAULT_AUTO_FIELD = (
    "django.db.models.BigAutoField"
)



AUTH_USER_MODEL = "users.User"