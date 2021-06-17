Settings
========

Rosetta can be configured via the following parameters, to be defined in your project settings file:

* ``ROSETTA_MESSAGES_PER_PAGE``: Number of messages to display per page. Defaults to ``10``.
* ``ROSETTA_ENABLE_TRANSLATION_SUGGESTIONS``: Enable AJAX translation suggestions. Defaults to ``False``.
* ``YANDEX_TRANSLATE_KEY``: Translation suggestions from Yandex `Yandex.Translate API <http://api.yandex.com/translate/>`_. To use this service you must first `obtain an AppID key <http://api.yandex.com/key/form.xml?service=trnsl>`_, then specify the key here. Defaults to ``None``.
* ``AZURE_CLIENT_SECRET``: Translation suggestions using the Microsoft Azure Translator API. To use this service, you must first `register for the service <https://docs.microsoft.com/en-us/azure/cognitive-services/Translator/translator-text-how-to-signup>`_, and set ``AZURE_CLIENT_SECRET`` to either of the keys listed for your subscription. Defaults to ``None``.
* ``DEEPL_AUTH_KEY``: Translation suggestions using the DeepL Translation API. To use this service, you must first `register for DeepL API <https://www.deepl.com/pro#developer>`_, and set ``DEEPL_AUTH_KEY`` to either of the keys listed for your subscription. Defaults to ``None``.
* ``DEEPL_LANGUAGES``: A dictionary to convert Django language codes to DeepL API Language codes. For example, for Simplified Chinese you could specify: ``{"zh_Hans": "ZH"}``. Check the languages supported by DeepL at `DeepL API docs <https://www.deepl.com/docs-api/>`_. Even if this is not set, Rosetta will try to get the language looking at the first 2 letters of django language code, but it would be useful if you want to specify EN-GB or EN-US for example.
* ``GOOGLE_APPLICATION_CREDENTIALS_PATH`` and ``GOOGLE_PROJECT_ID``: Translation suggestions using Google Translation API. To use this service, you must first `register the project <https://cloud.google.com/translate/docs/quickstart-client-libraries-v3>`_. You do not have to register ENV variable. GOOGLE_APPLICATION_CREDENTIALS_PATH is path to JSON credentials file. Defaults to ``None``. You also have to install google-cloud-translate package `pip install google-cloud-translate==3.0.2`
* ``ROSETTA_MESSAGES_SOURCE_LANGUAGE_CODE`` and ``ROSETTA_MESSAGES_SOURCE_LANGUAGE_NAME``: Change these if the source language in your PO files isn't English. Default to ``'en'`` and ``'English'`` respectively.
* ``ROSETTA_WSGI_AUTO_RELOAD`` and ``ROSETTA_UWSGI_AUTO_RELOAD``: When running WSGI daemon mode, using ``mod_wsgi`` 2.0c5 or later, this setting controls whether the contents of the gettext catalog files should be automatically reloaded by the WSGI processes each time they are modified. For performance reasons, this setting should be disabled in production environments. Default to ``False``.
* ``ROSETTA_EXCLUDED_APPLICATIONS``: Exclude applications defined in this list from being translated. Defaults to ``()``.
* ``ROSETTA_REQUIRES_AUTH``: Require authentication for all Rosetta views. Defaults to ``True``.
* ``ROSETTA_POFILE_WRAP_WIDTH``: Sets the line-length of the edited PO file. Set this to ``0`` to mimic ``makemessage``'s ``--no-wrap`` option. Defaults to ``78``.
* ``ROSETTA_STORAGE_CLASS``: See the note below on Storages. Defaults to ``rosetta.storage.CacheRosettaStorage``
* ``ROSETTA_ACCESS_CONTROL_FUNCTION``: An alternative function (string or a callable) that determines if a given user can access the translation views. This function receives a ``user`` as its argument, and returns a boolean specifying whether the passed user is allowed to use Rosetta or not.
* ``ROSETTA_LANGUAGE_GROUPS``: Set to ``True`` to enable language-specific groups, which can be used to give different translators access to different languages. Instead of creating a global ``translators`` group, create individual per-language groups, e.g. ``translators-de``, ``translators-fr``, and assign users to these.
* ``ROSETTA_CACHE_NAME``: When using ``rosetta.storage.CacheRosettaStorage``, you can store the Rosetta data in a specific cache. This is particularly useful when your ``default`` cache is a ``django.core.cache.backends.dummy.DummyCache`` (which happens on pre-production environments). If unset, it will default to ``rosetta`` if a cache with this name exists, or ``default`` if not.
* ``ROSETTA_POFILENAMES``: Defines which po file names are exposed in the web interface. Defaults to ``('django.po', 'djangojs.po')``
* ``ROSETTA_EXCLUDED_PATHS``: Exclude paths defined in this list from being searched (usually ends with "locale"). Defaults to ``()``
* ``ROSETTA_AUTO_COMPILE``: Determines whether the MO file is automatically compiled when the PO file is saved. Defaults to ``True``.
* ``ROSETTA_ENABLE_REFLANG``: Enables a selector for picking a reference language other than English. Defaults to ``False``.
* ``ROSETTA_SHOW_AT_ADMIN_PANEL``: Adds a handy link to Rosetta at the bottom of the Django admin apps index. Defaults to ``False``.
* ``ROSETTA_LOGIN_URL``: Use this if you want to override the login URL for rosetta. Defaults to ``settings.LOGIN_URL``.
* ``ROSETTA_LANGUAGES``: List of languages that Rosetta will offer to translate. This is useful when you wish to translate a language that is not yet defined in ``settings.LANGUAGES``. Defaults to ``settings.LANGUAGES``.
* ``ROSETTA_SHOW_OCCURRENCES``: Determines whether occurrences (where the original text appears) should be shown next to the translations for context. Defaults to ``True``.




Storages
--------

To prevent re-reading and parsing the PO file catalogs over and over again, Rosetta stores them in a volatile location. This can be either the HTTP session or the Django cache.

Django 1.4 has introduced a signed cookie session backend, which stores the whole content of the session in an encrypted cookie. Unfortunately this doesn't work with large PO files, as the limit of 4096 chars that can be stored in a cookie is easily exceeded.

In this case the Cache-based backend should be used (by setting ``ROSETTA_STORAGE_CLASS = 'rosetta.storage.CacheRosettaStorage'``). Please make sure that a proper ``CACHES`` backend is configured in your Django settings if your Django app is being served in a multi-process environment, or the different server processes, serving subsequent requests, won't find the storage data left by previous requests.

Alternatively you can switch back to using the Session based storage by setting ``ROSETTA_STORAGE_CLASS = 'rosetta.storage.SessionRosettaStorage'`` in your settings. This is perfectly safe on Django 1.3. On Django 1.4 or higher make sure you have DON'T use the `signed_cookies <https://docs.djangoproject.com/en/dev/topics/http/sessions/#using-cookie-based-sessions>`_ ``SESSION_BACKEND`` with this Rosetta storage backend or funky things might happen.

**TL;DR**: if you run Django with gunicorn, mod-wsgi or other multi-process environment, the Django-default ``CACHES`` ``LocMemCache`` backend won't suffice: use memcache instead, or you will run into issues.
