Settings
========

Rosetta can be configured via the following parameters, to be defined in your project settings file:

* ``ROSETTA_MESSAGES_PER_PAGE``: Number of messages to display per page. Defaults to ``10``.
* ``ROSETTA_ENABLE_TRANSLATION_SUGGESTIONS``: Enable AJAX translation suggestions. Defaults to ``False``.
* ``YANDEX_TRANSLATE_KEY``: Translation suggestions from Yandex `Yandex.Translate API <http://api.yandex.com/translate/>`_. To use this service you must first `obtain an AppID key <http://api.yandex.com/key/form.xml?service=trnsl>`_, then specify the key here. Defaults to ``None``.
* ``ROSETTA_GOOGLE_TRANSLATE``: Translation suggestions via the `Free Google Translate API <http://pythonhosted.org/goslate/>`_. You'll have to `pip install goslate`. Defaults to ``False``.
* ``AZURE_CLIENT_ID`` and ``AZURE_CLIENT_SECRET``: Translation suggestions using the Microsoft Azure API. To use this service, you must first `register for the service <https://datamarket.azure.com/dataset/5BA839F1-12CE-4CCE-BF57-A49D98D29A44>`_, then specify the 'Customer ID' and 'Primary Account Key' respectively, which you can find on your `account information page on Azure Marketplace <https://datamarket.azure.com/account?lang=en>`_.
* ``ROSETTA_MESSAGES_SOURCE_LANGUAGE_CODE`` and ``ROSETTA_MESSAGES_SOURCE_LANGUAGE_NAME``: Change these if the source language in your PO files isn't English. Default to ``'en'`` and ``'English'`` respectively.
* ``ROSETTA_WSGI_AUTO_RELOAD`` and ``ROSETTA_UWSGI_AUTO_RELOAD``: When running WSGI daemon mode, using ``mod_wsgi`` 2.0c5 or later, this setting controls whether the contents of the gettext catalog files should be automatically reloaded by the WSGI processes each time they are modified. For performance reasons, this setting should be disabled in production environments. Default to ``False``.
* ``ROSETTA_EXCLUDED_APPLICATIONS``: Exclude applications defined in this list from being translated. Defaults to ``()``.
* ``ROSETTA_REQUIRES_AUTH``: Require authentication for all Rosetta views. Defaults to ``True``.
* ``ROSETTA_POFILE_WRAP_WIDTH``: Sets the line-length of the edited PO file. Set this to ``0`` to mimic ``makemessage``'s ``--no-wrap`` option. Defaults to ``78``.
* ``ROSETTA_STORAGE_CLASS``: See the note below on Storages. Defaults to ``rosetta.storage.CacheRosettaStorage``
* ``ROSETTA_ACCESS_CONTROL_FUNCTION``: An alternative function that determines if a given user can access the translation views. This function receives a ``user`` as its argument, and returns a boolean specifying whether the passed user is allowed to use Rosetta or not.
* ``ROSETTA_LANGUAGE_GROUPS``: Set to ``True`` to enable language-specific groups, which can be used to give different translators access to different languages. Instead of creating a global ``translators`` group, create individual per-language groups, e.g. ``translators-de``, ``translators-fr``, and assign users to these.
* ``ROSETTA_CACHE_NAME``: When using ``rosetta.storage.CacheRosettaStorage``, you can store the Rosetta data in a specific cache. This is particularly useful when your ``default`` cache is a ``django.core.cache.backends.dummy.DummyCache`` (which happens on pre-production environments). If unset, it will default to ``rosetta`` if a cache with this name exists, or ``default`` if not.
* ``ROSETTA_POFILENAMES``: Defines which po file names are exposed in the web interface. Defaults to ``('django.po', 'djangojs.po')``
* ``ROSETTA_EXCLUDE_PATHS``: Exclude paths defined in this list from being searched (usually ends with "locale"). Defaults to ``()``


Storages
--------

To prevent re-reading and parsing the PO file catalogs over and over again, Rosetta stores them in a volatile location. This can be either the HTTP session or the Django cache.

Django 1.4 has introduced a signed cookie session backend, which stores the whole content of the session in an encrypted cookie. Unfortunately this doesn't work with large PO files, as the limit of 4096 chars that can be stored in a cookie is easily exceeded.

In this case the Cache-based backend should be used (by setting ``ROSETTA_STORAGE_CLASS = 'rosetta.storage.CacheRosettaStorage'``). Please make sure that a proper ``CACHES`` backend is configured in your Django settings if your Django app is being served in a multi-process environment, or the different server processes, serving subsequent requests, won't find the storage data left by previous requests.

Alternatively you can switch back to using the Session based storage by setting ``ROSETTA_STORAGE_CLASS = 'rosetta.storage.SessionRosettaStorage`` in your settings. This is perfectly safe on Django 1.3. On Django 1.4 or higher make sure you have DON'T use the `signed_cookies <https://docs.djangoproject.com/en/dev/topics/http/sessions/#using-cookie-based-sessions>`_ ``SESSION_BACKEND`` with this Rosetta storage backend or funky things might happen.

**TL;DR**: if you run Django with gunincorn, mod-wsgi or other multi-process environment, the Django-default ``CACHES`` ``LocMemCache`` backend won't suffice: use memcache instead, or you will run into issues.
