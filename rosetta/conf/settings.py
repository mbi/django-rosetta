from django.conf import settings

# Number of messages to display per page.
MESSAGES_PER_PAGE = getattr(settings, 'ROSETTA_MESSAGES_PER_PAGE', 10)


# Enable Google translation suggestions
ENABLE_TRANSLATION_SUGGESTIONS = getattr(settings, 'ROSETTA_ENABLE_TRANSLATION_SUGGESTIONS', False)


# Can be obtained for free here: https://translate.yandex.com/apikeys
YANDEX_TRANSLATE_KEY = getattr(settings, 'YANDEX_TRANSLATE_KEY', None)

# See here to obtain a free Azure key and enable the Translator Text service:
# https://docs.microsoft.com/en-us/azure/cognitive-services/Translator/translator-text-how-to-signup
AZURE_CLIENT_SECRET = getattr(settings, 'AZURE_CLIENT_SECRET', None)

# Displays this language beside the original MSGID in the admin
MAIN_LANGUAGE = getattr(settings, 'ROSETTA_MAIN_LANGUAGE', None)

# Change these if the source language in your PO files isn't English
MESSAGES_SOURCE_LANGUAGE_CODE = getattr(settings, 'ROSETTA_MESSAGES_SOURCE_LANGUAGE_CODE', 'en')
MESSAGES_SOURCE_LANGUAGE_NAME = getattr(settings, 'ROSETTA_MESSAGES_SOURCE_LANGUAGE_NAME', 'English')

ACCESS_CONTROL_FUNCTION = getattr(
    settings, 'ROSETTA_ACCESS_CONTROL_FUNCTION', None)


"""
When running WSGI daemon mode, using mod_wsgi 2.0c5 or later, this setting
controls whether the contents of the gettext catalog files should be
automatically reloaded by the WSGI processes each time they are modified.

Notes:

 * The WSGI daemon process must have write permissions on the WSGI script file
   (as defined by the WSGIScriptAlias directive.)
 * WSGIScriptReloading must be set to On (it is by default)
 * For performance reasons, this setting should be disabled in production environments
 * When a common rosetta installation is shared among different Django projects,
   each one running in its own distinct WSGI virtual host, you can activate
   auto-reloading in individual projects by enabling this setting in the project's
   own configuration file, i.e. in the project's settings.py

Refs:

 * http://code.google.com/p/modwsgi/wiki/ReloadingSourceCode
 * http://code.google.com/p/modwsgi/wiki/ConfigurationDirectives#WSGIReloadMechanism

"""
WSGI_AUTO_RELOAD = getattr(settings, 'ROSETTA_WSGI_AUTO_RELOAD', False)
UWSGI_AUTO_RELOAD = getattr(settings, 'ROSETTA_UWSGI_AUTO_RELOAD', False)


# Exclude applications defined in this list from being translated
EXCLUDED_APPLICATIONS = getattr(settings, 'ROSETTA_EXCLUDED_APPLICATIONS', ())

# Line length of the updated PO file
POFILE_WRAP_WIDTH = getattr(settings, 'ROSETTA_POFILE_WRAP_WIDTH', 78)

# Storage class to handle temporary data storage
STORAGE_CLASS = getattr(settings, 'ROSETTA_STORAGE_CLASS', 'rosetta.storage.CacheRosettaStorage')

ENABLE_REFLANG = getattr(settings, 'ROSETTA_ENABLE_REFLANG', False)

# Allow overriding of the default filenames, you mostly won't need to change this
POFILENAMES = getattr(settings, 'ROSETTA_POFILENAMES', ('django.po', 'djangojs.po'))

ROSETTA_CACHE_NAME = getattr(settings, 'ROSETTA_CACHE_NAME', 'rosetta'
                             if 'rosetta' in settings.CACHES else 'default')

# Require users to be authenticated (and Superusers or in group "translators").
# Set this to False at your own risk
ROSETTA_REQUIRES_AUTH = getattr(settings, 'ROSETTA_REQUIRES_AUTH', True)

# Exclude paths defined in this list from being searched (usually ends with "locale")
ROSETTA_EXCLUDED_PATHS = getattr(settings, 'ROSETTA_EXCLUDED_PATHS', ())

# Set to True to enable language-specific groups, which can be used to give
# different translators access to different languages. Instead of creating a
# 'translators` group, create individual per-language groups, e.g.
# 'translators-de', 'translators-fr', ...
ROSETTA_LANGUAGE_GROUPS = getattr(settings, 'ROSETTA_LANGUAGE_GROUPS', False)

# Determines whether the MO file is automatically compiled when the PO file is saved.
AUTO_COMPILE = getattr(settings, 'ROSETTA_AUTO_COMPILE', True)

SHOW_AT_ADMIN_PANEL = getattr(settings, 'ROSETTA_SHOW_AT_ADMIN_PANEL', False)
