import os
import sys

import django


SITE_ID = 1

PROJECT_PATH = os.path.abspath(os.path.dirname(__file__))

PYTHON_VERSION = '%s.%s' % sys.version_info[:2]

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(PROJECT_PATH, 'rosetta.db'),
    }
}

if django.VERSION[:3] >= (3, 2, 0):
    CACHES = {
        'default': {
            'BACKEND': 'django.core.cache.backends.memcached.PyMemcacheCache',
            'LOCATION': '127.0.0.1:11211',
            'KEY_PREFIX': 'ROSETTA_TEST',
        }
    }
else:
    CACHES = {
        'default': {
            'BACKEND': 'django.core.cache.backends.memcached.MemcachedCache',
            'LOCATION': '127.0.0.1:11211',
            'KEY_PREFIX': 'ROSETTA_TEST',
        }
    }

# CACHES = {'default': {'BACKEND': 'django.core.cache.backends.dummy.DummyCache'}}

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
    'django.contrib.messages',
    'rosetta',
]

if django.VERSION[0:2] >= (1, 7):
    INSTALLED_APPS.append('rosetta.tests.test_app.apps.TestAppConfig')

LANGUAGE_CODE = "en"

MIDDLEWARE = (
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
)

# Note: languages are overridden in the test runner
LANGUAGES = (
    ('en', u'English'),
    ('bs-Cyrl-BA', u'Bosnian (Cyrillic) (Bosnia and Herzegovina)'),
    ('ja', u'日本語'),
    ('xx', u'XXXXX'),
    ('fr', u'French'),
    ('zh_Hans', u'Chinese (Simplified)'),
    ('fr_FR.utf8', u'French (France), UTF8'),
)

SILENCED_SYSTEM_CHECKS = ["translation.E002"]


LOCALE_PATHS = [os.path.join(PROJECT_PATH, 'locale')]

SOUTH_TESTS_MIGRATE = False

FIXTURE_DIRS = (os.path.join(PROJECT_PATH, 'fixtures'),)
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
                "django.contrib.messages.context_processors.messages",
                "django.template.context_processors.request",
            ),
        },
    }
]

STATIC_URL = '/static/'

# SESSION_ENGINE = "django.contrib.sessions.backends.signed_cookies"
# ROSETTA_STORAGE_CLASS = 'rosetta.storage.SessionRosettaStorage'

ROSETTA_STORAGE_CLASS = 'rosetta.storage.CacheRosettaStorage'
SECRET_KEY = 'empty'

ROSETTA_ENABLE_REFLANG = True
ROSETTA_ENABLE_TRANSLATION_SUGGESTIONS = True
ROSETTA_SHOW_AT_ADMIN_PANEL = True
# ROSETTA_SHOW_OCCURRENCES = True

# fake azure key that matches the one in
# fixtures/vcr_cassettes/test_47_azure_ajax_translation.yaml
AZURE_CLIENT_SECRET = 'FAKE'
