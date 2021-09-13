import os
import sys

import django

from rosetta.views import find_all_locale

SITE_ID = 1

PROJECT_PATH = os.path.abspath(os.path.dirname(__file__))

PYTHON_VERSION = "%s.%s" % sys.version_info[:2]

LOGIN_URL = "/admin/login"
ROSETTA_REQUIRES_AUTH = False
ROSETTA_LANGUAGE_GROUPS = ["translators-es"]

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": os.path.join(PROJECT_PATH, "rosetta.db"),
    }
}

if django.VERSION[:3] >= (3, 2, 0):
    CACHES = {
        "default": {
            "BACKEND": "django.core.cache.backends.memcached.PyMemcacheCache",
            "LOCATION": "127.0.0.1:11211",
            "KEY_PREFIX": "ROSETTA_TEST",
        }
    }
else:
    CACHES = {
        "default": {
            "BACKEND": "django.core.cache.backends.memcached.MemcachedCache",
            "LOCATION": "127.0.0.1:11211",
            "KEY_PREFIX": "ROSETTA_TEST",
        }
    }

# CACHES = {'default': {'BACKEND': 'django.core.cache.backends.dummy.DummyCache'}}

TEST_DATABASE_CHARSET = "utf8"
TEST_DATABASE_COLLATION = "utf8_general_ci"

DATABASE_SUPPORTS_TRANSACTIONS = True
SETTINGS_MODULE = "testproject.settings"

INSTALLED_APPS = [
    "django.contrib.auth",
    "django.contrib.admin",
    # 'django.contrib.admin.apps.SimpleAdminConfig',
    # 'django.contrib.redirects.apps.RedirectsConfig',
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.sites",
    "django.contrib.messages",
    "rosetta",
]

if django.VERSION[0:2] >= (1, 7):
    INSTALLED_APPS.append("rosetta.tests.test_app.apps.TestAppConfig")

LANGUAGE_CODE = "en"

MIDDLEWARE = (
    "django.middleware.common.CommonMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
)

# Note: languages are overridden in the test runner
LANGUAGES = (
    ("en", "English"),
    ("fi-fi", "Finnish"),
    ("it", "Italian"),
    ("ja-jp", "Japanese"),
    ("pt-br", "Portuguese (Brazil)"),
    ("pt-pt", "Portuguese (Portugal)"),
    ("ru", "Russian"),
    ("sv-se", "Swedish"),
    ("zh-hans", "Simplified Chinese"),
    ("es", "Spanish"),
)


SILENCED_SYSTEM_CHECKS = ["translation.E002"]

TRANSLATE_PROJECT_PATH = "/home/jyoost/PycharmProjects/shuuproll/shuup/"
if TRANSLATE_PROJECT_PATH:
    LOCALE_PATHS = find_all_locale(TRANSLATE_PROJECT_PATH)
else:
    LOCALE_PATHS = [
        os.path.join(TRANSLATE_PROJECT_PATH, "shuup/front/apps/carousel/locale"),
        os.path.join(
            TRANSLATE_PROJECT_PATH, "shuup/front/apps/recently_viewed_products/locale"
        ),
        """
         os.path.join(TRANSLATE_PROJECT_PATH, "shuup/front/apps/customer_information/locale"),
         os.path.join(TRANSLATE_PROJECT_PATH, "shuup/front/apps/registration/locale"),
         os.path.join(TRANSLATE_PROJECT_PATH, "shuup/front/apps/saved_carts/locale"),
         os.path.join(TRANSLATE_PROJECT_PATH, "shuup/front/apps/simple_search/locale"),
         os.path.join(TRANSLATE_PROJECT_PATH, "shuup/front/apps/simple_order_notification/locale"),
         os.path.join(TRANSLATE_PROJECT_PATH, "shuup/front/apps/personal_order_history/locale"),
         os.path.join(TRANSLATE_PROJECT_PATH, "shuup/front/apps/auth/locale"),
         os.path.join(TRANSLATE_PROJECT_PATH, "shuup/front/node_modules/moment/dist/locale"),
         os.path.join(TRANSLATE_PROJECT_PATH, "shuup/front/node_modules/moment/locale"),
         os.path.join(TRANSLATE_PROJECT_PATH, "shuup/front/node_modules/moment/src/locale"),
         os.path.join(TRANSLATE_PROJECT_PATH, "shuup/front/node_modules/moment/src/lib/locale"),
         os.path.join(TRANSLATE_PROJECT_PATH, "shuup/front/locale"),
         os.path.join(TRANSLATE_PROJECT_PATH, "shuup/xtheme/locale"),
         os.path.join(TRANSLATE_PROJECT_PATH, "shuup/admin/node_modules/moment/locale"),
         os.path.join(TRANSLATE_PROJECT_PATH, "shuup/admin/node_modules/moment/src/locale"),
         os.path.join(TRANSLATE_PROJECT_PATH, "shuup/admin/node_modules/moment/src/lib/locale"),
         os.path.join(TRANSLATE_PROJECT_PATH, "shuup/admin/locale"),
         os.path.join(TRANSLATE_PROJECT_PATH, "shuup/default_reports/locale"),
         os.path.join(TRANSLATE_PROJECT_PATH, "shuup/addons/locale"),
         os.path.join(TRANSLATE_PROJECT_PATH, "shuup/themes/classic_gray/locale"),
         os.path.join(TRANSLATE_PROJECT_PATH, "shuup/importer/locale"),
         os.path.join(TRANSLATE_PROJECT_PATH, "shuup/customer_group_pricing/locale"),
         os.path.join(TRANSLATE_PROJECT_PATH, "shuup/default_importer/locale"),
         os.path.join(TRANSLATE_PROJECT_PATH, "shuup/reports/locale"),
         os.path.join(TRANSLATE_PROJECT_PATH, "shuup/gdpr/locale"),
         os.path.join(TRANSLATE_PROJECT_PATH, "shuup/campaigns/locale"),
         os.path.join(TRANSLATE_PROJECT_PATH, "shuup/utils/locale"),
         os.path.join(TRANSLATE_PROJECT_PATH, "shuup/simple_supplier/locale"),
         os.path.join(TRANSLATE_PROJECT_PATH, "shuup/simple_cms/locale"),
         os.path.join(TRANSLATE_PROJECT_PATH, "shuup/order_printouts/locale"),
         os.path.join(TRANSLATE_PROJECT_PATH, "shuup/notify/locale"),
         os.path.join(TRANSLATE_PROJECT_PATH, "shuup/locale"),
         os.path.join(TRANSLATE_PROJECT_PATH, "shuup/guide/locale"),
         os.path.join(TRANSLATE_PROJECT_PATH, "shuup/testing/locale"),
         os.path.join(TRANSLATE_PROJECT_PATH, "shuup/default_tax/locale"),
         os.path.join(TRANSLATE_PROJECT_PATH, "shuup/tasks/locale"),
         os.path.join(TRANSLATE_PROJECT_PATH, "shuup/core/locale"),
         os.path.join(TRANSLATE_PROJECT_PATH, "shuup/discounts/locale"),
         """,
    ]

SOUTH_TESTS_MIGRATE = False

FIXTURE_DIRS = (os.path.join(PROJECT_PATH, "fixtures"),)
STATIC_URL = "/static/"
ROOT_URLCONF = "testproject.urls"

DEBUG = True

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "APP_DIRS": True,
        "OPTIONS": {
            "debug": False,
            "context_processors": (
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

STATIC_URL = "/static/"

# SESSION_ENGINE = "django.contrib.sessions.backends.signed_cookies"
# ROSETTA_STORAGE_CLASS = 'rosetta.storage.SessionRosettaStorage'

ROSETTA_STORAGE_CLASS = "rosetta.storage.CacheRosettaStorage"
SECRET_KEY = "empty"

ROSETTA_ENABLE_REFLANG = True
ROSETTA_ENABLE_TRANSLATION_SUGGESTIONS = True
ROSETTA_SHOW_AT_ADMIN_PANEL = True
# ROSETTA_SHOW_OCCURRENCES = True
# for addon
PATH_TO_POEDIT = "/snap/bin/poedit"
# fake azure key that matches the one in
# fixtures/vcr_cassettes/test_47_azure_ajax_translation.yaml
AZURE_CLIENT_SECRET = None  # "FAKE"


DEEPL_AUTH_KEY = "f5550784-a393-086f-072e-ba813c3f03ff:fx"


# Deepl API language codes are different then those of django, so if this is not set according to your desired languages,
# We use the uppercase version of the first 2 letters of django language code.
# In which case it would work fine for most of the languages,
# But for 'en' if you want "EN-GB" for example, please set it in this dictionary.
# Please check the supported languages list of DeepL API: https://www.deepl.com/docs-api/translating-text/request/
DEEPL_LANGUAGES = {"fr": "FR", "en": "EN-US", "zh_Hans": "ZH", "es": "ES", "ar": "AR"}
