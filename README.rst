=======
Rosetta
=======

Rosetta is a `Django <http://www.djangoproject.com/>`_ application that eases the translation process of your Django projects.

Because it doesn't export any models, Rosetta doesn't create any tables in your project's database. Rosetta can be installed and uninstalled by simply adding and removing a single entry in your project's `INSTALLED_APPS` and a single line in your main ``urls.py`` file. 

********
Features
********

* Database independent 
* Reads and writes your project's `gettext` catalogs (po and mo files)
* Installed and uninstalled in under a minute
* Uses Django's admin interface CSS


************
Requirements
************

Rosetta requires Django 1.3, 1.4 or 1.5. When running with Django 1.5, Python 3.x is supported.

************
Installation
************


To install Rosetta:

1. ``pip install django-rosetta``
2. Add ``'rosetta'`` to the `INSTALLED_APPS` in your project's ``settings.py``
3. Add an URL entry to your project's ``urls.py``, for example::

    from django.conf import settings
    
    if 'rosetta' in settings.INSTALLED_APPS:
        urlpatterns += patterns('',
            url(r'^rosetta/', include('rosetta.urls')),
        )



Note: you can use whatever you wish as the URL prefix.

To uninstall Rosetta, simply comment out or remove the ``'rosetta'`` line in your ``INSTALLED_APPS``

*************
Configuration
*************

Rosetta can be configured via the following parameters, to be defined in your project settings file:

* ``ROSETTA_MESSAGES_PER_PAGE``: Number of messages to display per page. Defaults to ``10``.
* ``ROSETTA_ENABLE_TRANSLATION_SUGGESTIONS``: Enable AJAX translation suggestions. Defaults to ``False``.
* ``BING_APP_ID``: Translation suggestions used to come from the Google Translation API service, but free service has been discontinued, and the next best thing is Microsoft `Bing's Translation API <http://msdn.microsoft.com/en-us/library/ff512404.aspx>`_. To use this service you must first `obtain an AppID key <https://ssl.bing.com/webmaster/Developers/AppIds/>`_, then specify the key here. Defaults to ``None``.
* ``ROSETTA_MESSAGES_SOURCE_LANGUAGE_CODE`` and ``ROSETTA_MESSAGES_SOURCE_LANGUAGE_NAME``: Change these if the source language in your PO files isn't English. Default to ``'en'`` and ``'English'`` respectively.
* ``ROSETTA_WSGI_AUTO_RELOAD`` and ``ROSETTA_UWSGI_AUTO_RELOAD``: When running WSGI daemon mode, using ``mod_wsgi`` 2.0c5 or later, this setting controls whether the contents of the gettext catalog files should be automatically reloaded by the WSGI processes each time they are modified. For performance reasons, this setting should be disabled in production environments. Default to ``False``.
* ``ROSETTA_EXCLUDED_APPLICATIONS``: Exclude applications defined in this list from being translated. Defaults to ``()``.
* ``ROSETTA_REQUIRES_AUTH``: Require authentication for all Rosetta views. Defaults to ``True``.
* ``ROSETTA_POFILE_WRAP_WIDTH``: Sets the line-length of the edited PO file. Set this to ``0`` to mimic ``makemessage``'s ``--no-wrap`` option. Defaults to ``78``.
* ``ROSETTA_STORAGE_CLASS``: See the note below on Storages. Defaults to ``rosetta.storage.CacheRosettaStorage``

********
Storages
********

To prevent re-reading and parsing the PO file catalogs over and over again, Rosetta stores them in a volatile location. This can be either the HTTP session or the Django cache. 

Django 1.4 has introduced a signed cookie session backend, which stores the whole content of the session in an encrypted cookie. Unfortunately this doesn't work with large PO files, as the limit of 4096 chars that can be stored in a cookie are easily exceeded. 

In this case the Cache-based backend should be used (by setting ``ROSETTA_STORAGE_CLASS = 'rosetta.storage.CacheRosettaStorage'``). Please make sure that a proper CACHES backend is configured in your Django settings.

Alternatively you can switch back to using the Session based storage by setting ``ROSETTA_STORAGE_CLASS = 'rosetta.storage.SessionRosettaStorage`` in your settings. This is perfectly safe on Django 1.3. On Django 1.4 or higher make sure you have DON'T use the `signed_cookies <https://docs.djangoproject.com/en/dev/topics/http/sessions/#using-cookie-based-sessions>`_ ``SESSION_BACKEND`` with this Rosetta storage backend or funky things might happen.

********
Security
********

Because Rosetta requires write access to some of the files in your Django project, access to the application is restricted to the administrator user only (as defined in your project's Admin interface)

If you wish to grant editing access to other users:
 
1. Create a 'translators' group in your admin interface
2. Add the user you wish to grant translating rights to this group

*****
Usage
*****

Generate a batch of files to translate
--------------------------------------

See `Django's documentation on Internationalization <https://docs.djangoproject.com/en/dev/topics/i18n/translation/>`_ to setup your project to use i18n and create the ``gettext`` catalog files.

Translate away!
---------------

Start your Django development server and point your browser to the URL prefix you have chosen during the installation process. You will get to the file selection window.

.. image:: http://django-rosetta.googlecode.com/files/rosetta-1.png

Select a file and translate each untranslated message. Whenever a new batch of messages is processed, Rosetta updates the corresponding `django.po` file and regenerates the corresponding ``mo`` file.

This means your project's labels will be translated right away, unfortunately you'll still have to restart the webserver for the changes to take effect. (NEW: if your webserver supports it, you can force auto-reloading of the translated catalog whenever a change was saved. See the note regarding the ``ROSETTA_WSGI_AUTO_RELOAD`` variable in ``conf/settings.py``.

If the webserver doesn't have write access on the catalog files (as shown in the screen shot below) an archive of the catalog files can be downloaded.

.. image:: http://django-rosetta.googlecode.com/files/rosetta-2.1.png


Translating Rosetta itself
--------------------------

By default Rosetta hides its own catalog files in the file selection interface (shown above.) If you would like to translate Rosetta to your own language:

1. Create a subdirectory for your locale inside Rosetta's ``locale`` directory, e.g. ``rosetta/locale/XX/LC_MESSAGES``
2. Instruct Django to create the initial catalog, by running ``django-admin.py  makemessages -l XX`` inside Rosetta's directory (refer to `Django's documentation on i18n <http://www.djangoproject.com/documentation/i18n/>`_ for details)
3. Instruct Rosetta to look for its own catalogs, by appending `?rosetta` to the language selection page's URL, e.g. ``http://127.0.0.1:8000/rosetta/pick/?rosetta``
4. Translate as usual
5. Send a pull request if you feel like sharing




***************
Acknowledgments
***************

* Rosetta uses the excellent `polib <http://code.google.com/p/polib/>`_ library to parse and handle gettext files.

