# -*- coding: utf-8 -*-
import django
import os
import sys

SITE_ID = 1

PROJECT_PATH = os.path.abspath(os.path.dirname(__file__))

PYTHON_VERSION = '%s.%s' % sys.version_info[:2]
DJANGO_VERSION = django.get_version()

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(PROJECT_PATH, 'rosetta.db')
    }
}

TEST_DATABASE_CHARSET = "utf8"
TEST_DATABASE_COLLATION = "utf8_general_ci"

DATABASE_SUPPORTS_TRANSACTIONS = True

INSTALLED_APPS = [
    'django.contrib.auth',
    'django.contrib.admin',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',

    'rosetta',
]

LANGUAGE_CODE = "en"

LANGUAGES = (
    ('en', 'English'),
    ('ja', u'日本語'),
    ('xx', u'XXXXX'),
)

SOUTH_TESTS_MIGRATE = False

FIXTURE_DIRS = (
    os.path.join(PROJECT_PATH, 'fixtures'),
)
STATIC_URL = '/static/'
ROOT_URLCONF = 'testproject.urls'

DEBUG = True
TEMPLATE_DEBUG = True
SESSION_ENGINE = "django.contrib.sessions.backends.signed_cookies"
