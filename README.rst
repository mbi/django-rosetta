=Rosetta=

Rosetta is a [http://www.djangoproject.com/ Django] application that eases the translation process of your Django projects.

Because it doesn't export any models, Rosetta doesn't create any tables in your project's database. Rosetta can be installed and uninstalled by simply adding and removing a single entry in your project's `INSTALLED_APPS` and a single line in your main `urls.py` file. 

==Features==
  * Database independent 
  * Reads and writes your project's `gettext` catalogs (po and mo files)
  * Installed and uninstalled in under a minute
  * Uses Django's admin interface CSS
  * Translation suggestions via [http://code.google.com/apis/ajaxlanguage/ Google AJAX Language API]

==Installation==

To install Rosetta:

  # [http://code.google.com/p/django-rosetta/downloads/list Download] the application and place the `rosetta` folder anywhere in your Python path (your project directory is fine, but anywhere else in your python path will do), or simply install  using setuptools: `sudo easy_install django-rosetta`
  # Add a `'rosetta'` line to  the `INSTALLED_APPS` in your project's `settings.py`
  # Add an URL entry to your project's `urls.py`, for example: 
{{{
from django.conf import settings
if 'rosetta' in settings.INSTALLED_APPS:
    urlpatterns += patterns('',
        url(r'^rosetta/', include('rosetta.urls')),
    )
}}}

Note: you can use whatever you wish as the URL prefix.

To uninstall Rosetta, simply comment out or remove the `'rosetta'` line in your `INSTALLED_APPS`

==Security==
Because Rosetta requires write access to some of the files in your Django project, access to the application is restricted to the administrator user only (as defined in your project's Admin interface)

If you wish to grant editing access to other users:
  # Create a 'translators' group in your admin interface
  # Add the user you wish to grant translating rights to this group

==Usage==

===Generate a batch of files to translate===
See [http://www.djangoproject.com/documentation/i18n/ Django's documentation on Internationalization] to setup your project to use i18n and create the `gettext` catalog files.

===Translate away!===
Start your Django development server and point your browser to the URL prefix you have chosen during the installation process. You will get to the file selection window.

http://django-rosetta.googlecode.com/files/rosetta-1.png

Select a file and translate each untranslated message. Whenever a new batch of messages is processed, Rosetta updates the corresponding `django.po` file and regenerates the corresponding `mo` file.

This means your project's labels will be translated right away, unfortunately you'll still have to restart the webserver for the changes to take effect. (NEW: if your webserver supports it, you can force auto-reloading of the translated catalog whenever a change was saved. See the note regarding the `ROSETTA_WSGI_AUTO_RELOAD` variable in [http://code.google.com/p/django-rosetta/source/browse/trunk/rosetta/conf/settings.py conf/settings.py].

If the webserver doesn't have write access on the catalog files (as shown in the screen shot below) an archive of the catalog files can be downloaded.

http://django-rosetta.googlecode.com/files/rosetta-2.1.png


===Translating Rosetta itself===
By default Rosetta hides its own catalog files in the file selection interface (shown above.) If you would like to translate Rosetta to your own language:

  # Create a subdirectory for your locale inside Rosetta's `locale` directory, e.g. `rosetta/locale/XX/LC_MESSAGES`
  # Instruct Django to create the initial catalog, by running ` django-admin.py  makemessages -l XX` inside Rosetta's directory (refer to [http://www.djangoproject.com/documentation/i18n/ Django's documentation on i18n] for details)
  # Instruct Rosetta to look for its own catalogs, by appending `?rosetta` to the language selection page's URL, e.g. `http://127.0.0.1:8000/rosetta/pick/?rosetta`
  # Translate as usual
  # Optionally, submit your translation for inclusion by [http://code.google.com/p/django-rosetta/issues/entry creating an issue and attaching your translated po file to the ticket]


==Acknowledgments==
  * Rosetta uses the excellent [http://code.google.com/p/polib/ polib] library to parse and handle Po files.

<wiki:gadget url="http://stefansundin.com/stuff/flattr/google-project-hosting.xml" border="0" width="66" height="76" up_uid="20885" up_title="Django Rosetta" up_desc="A Django application that eases the translation process of your Django projects" up_tags="django, rosetta, software, gettext, i18n, l10n" up_url="http://code.google.com/p/django-rosetta/" />


<wiki:gadget url="http://www.ohloh.net/p/18854/widgets/project_users.xml" height="100"  border="0" />