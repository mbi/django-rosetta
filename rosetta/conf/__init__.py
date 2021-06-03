"""
For a description of each rosetta setting see: docs/settings.rst.
"""

from django.conf import settings as dj_settings
from django.core.signals import setting_changed


__all__ = ['settings']


class RosettaSettings(object):
    """
    Class that holds rosetta settings.

    The settings object is an instance of this class and is reloaded when
    the ``setting_changed`` signal is dispatched.
    """

    SETTINGS = {
        'ROSETTA_MESSAGES_PER_PAGE': ('MESSAGES_PER_PAGE', 10),
        'ROSETTA_ENABLE_TRANSLATION_SUGGESTIONS': (
            'ENABLE_TRANSLATION_SUGGESTIONS',
            False,
        ),
        'YANDEX_TRANSLATE_KEY': ('YANDEX_TRANSLATE_KEY', None),
        'AZURE_CLIENT_SECRET': ('AZURE_CLIENT_SECRET', None),
        'GOOGLE_APPLICATION_CREDENTIALS_PATH': (
            'GOOGLE_APPLICATION_CREDENTIALS_PATH',
            None,
        ),
        'GOOGLE_PROJECT_ID': ('GOOGLE_PROJECT_ID', None),
        'DEEPL_AUTH_KEY': ('DEEPL_AUTH_KEY', None),
        'ROSETTA_MAIN_LANGUAGE': ('MAIN_LANGUAGE', None),
        'ROSETTA_MESSAGES_SOURCE_LANGUAGE_CODE': ('MESSAGES_SOURCE_LANGUAGE_CODE', 'en'),
        'ROSETTA_MESSAGES_SOURCE_LANGUAGE_NAME': (
            'MESSAGES_SOURCE_LANGUAGE_NAME',
            'English',
        ),
        'ROSETTA_ACCESS_CONTROL_FUNCTION': ('ACCESS_CONTROL_FUNCTION', None),
        'ROSETTA_WSGI_AUTO_RELOAD': ('WSGI_AUTO_RELOAD', False),
        'ROSETTA_UWSGI_AUTO_RELOAD': ('UWSGI_AUTO_RELOAD', False),
        'ROSETTA_EXCLUDED_APPLICATIONS': ('EXCLUDED_APPLICATIONS', ()),
        'ROSETTA_POFILE_WRAP_WIDTH': ('POFILE_WRAP_WIDTH', 78),
        'ROSETTA_STORAGE_CLASS': ('STORAGE_CLASS', 'rosetta.storage.CacheRosettaStorage'),
        'ROSETTA_ENABLE_REFLANG': ('ENABLE_REFLANG', False),
        'ROSETTA_POFILENAMES': ('POFILENAMES', ('django.po', 'djangojs.po')),
        'ROSETTA_CACHE_NAME': (
            'ROSETTA_CACHE_NAME',
            'rosetta' if 'rosetta' in dj_settings.CACHES else 'default',
        ),
        'ROSETTA_REQUIRES_AUTH': ('ROSETTA_REQUIRES_AUTH', True),
        'ROSETTA_EXCLUDED_PATHS': ('ROSETTA_EXCLUDED_PATHS', ()),
        'ROSETTA_LANGUAGE_GROUPS': ('ROSETTA_LANGUAGE_GROUPS', False),
        'ROSETTA_AUTO_COMPILE': ('AUTO_COMPILE', True),
        'ROSETTA_SHOW_AT_ADMIN_PANEL': ('SHOW_AT_ADMIN_PANEL', False),
        'ROSETTA_LOGIN_URL': ('LOGIN_URL', dj_settings.LOGIN_URL),
        'ROSETTA_LANGUAGES': ('ROSETTA_LANGUAGES', dj_settings.LANGUAGES),
        'ROSETTA_SHOW_OCCURRENCES': ('SHOW_OCCURRENCES', True),
        # Deepl API language codes are different then those of django, so if this is not set according to your desired languages,
        # We use the first 2 letters of django language code.
        # In which case it would work fine for most of the languages,
        # But for 'en' if you want "EN-GB" for example, please set it in this dictionary.
        # you can find the supported languages list of DeepL API here: https://www.deepl.com/docs-api/translating-text/request/
        # ex: DEEPL_LANGUAGES = {"fr": "FR", "en": "EN-GB", "zh_Hans": "ZH"}
        'DEEPL_LANGUAGES': ('DEEPL_LANGUAGES', {}),
    }

    def __init__(self):
        # make sure we don't assign self._settings directly here, to avoid
        # recursion in __setattr__, we delegate to the parent instead
        super(RosettaSettings, self).__setattr__('_settings', {})
        self.load()

    def load(self):
        for user_setting, (rosetta_setting, default) in self.SETTINGS.items():
            self._settings[rosetta_setting] = getattr(dj_settings, user_setting, default)

    def reload(self):
        self.__init__()

    def __getattr__(self, attr):
        if attr not in self._settings:
            raise AttributeError("'RosettaSettings' object has not attribute '%s'" % attr)
        return self._settings[attr]

    def __setattr__(self, attr, value):
        if attr not in self._settings:
            raise AttributeError("'RosettaSettings' object has not attribute '%s'" % attr)
        self._settings[attr] = value


# This is our global settings object
settings = RosettaSettings()


# Signal handler to reload settings when needed
def reload_settings(*args, **kwargs):
    val = kwargs.get('setting')
    if val in settings.SETTINGS:
        settings.reload()


# Connect the setting_changed signal to our handler
setting_changed.connect(reload_settings)
