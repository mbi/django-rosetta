# -*- coding: utf-8 -*-
#from __future__ import unicode_literals
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

CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.memcached.MemcachedCache',
        'LOCATION': '127.0.0.1:11211',
        'KEY_PREFIX': 'ROSETTA_TEST'
    }
}


#CACHES = {'default': {'BACKEND': 'django.core.cache.backends.dummy.DummyCache'}}

TEST_DATABASE_CHARSET = "utf8"
TEST_DATABASE_COLLATION = "utf8_general_ci"

DATABASE_SUPPORTS_TRANSACTIONS = True
SETTINGS_MODULE = 'testproject.settings'

INSTALLED_APPS = [
    'django.contrib.auth',
    'django.contrib.admin',
    # 'django.contrib.admin.apps.SimpleAdminConfig',
    # 'django.contrib.redirects.apps.RedirectsConfig',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'rosetta',
]

if django.VERSION[0:2] >= (1, 7):
    INSTALLED_APPS.append('rosetta.tests.test_app.apps.TestAppConfig')

LANGUAGE_CODE = "en"

MIDDLEWARE_CLASSES = (
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware'
)

LANGUAGES = (
    ('bs-Cyrl-BA', u'Bosnian (Cyrillic) (Bosnia and Herzegovina)'),
    ('ja', u'日本語'),
    ('xx', u'XXXXX'),
    ('fr', u'French'),
    ('fr_FR.utf8', u'French (France), UTF8'),
)

LOCALE_PATHS = [
    os.path.join(PROJECT_PATH, 'locale'),
]

SOUTH_TESTS_MIGRATE = False

FIXTURE_DIRS = (
    os.path.join(PROJECT_PATH, 'fixtures'),
)
STATIC_URL = '/static/'
ROOT_URLCONF = 'testproject.urls'

DEBUG = True

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'APP_DIRS': True,
        'OPTIONS': {
            'debug': False,
            'context_processors': (
                "django.contrib.auth.context_processors.auth",
                "django.template.context_processors.debug",
                "django.template.context_processors.i18n",
                "django.template.context_processors.media",
                "django.template.context_processors.static",
                "django.template.context_processors.tz",
                "django.contrib.messages.context_processors.messages"
            )
        }
    },
]

STATIC_URL = '/static/'
#SESSION_ENGINE = "django.contrib.sessions.backends.signed_cookies"
#ROSETTA_STORAGE_CLASS = 'rosetta.storage.SessionRosettaStorage'
ROSETTA_STORAGE_CLASS = 'rosetta.storage.CacheRosettaStorage'
SECRET_KEY = 'empty'

ROSETTA_GOOGLE_TRANSLATE = True
ROSETTA_ENABLE_TRANSLATION_SUGGESTIONS = True
