=======
Rosetta
=======

.. image:: https://travis-ci.org/mbi/django-rosetta.svg?branch=develop
  :target: http://travis-ci.org/mbi/django-rosetta
  
.. image:: https://img.shields.io/pypi/v/django-rosetta
  :target: https://pypi.org/project/django-rosetta/

.. image:: https://img.shields.io/pypi/l/django-rosetta
  :target: https://github.com/mbi/django-rosetta/blob/develop/LICENSE


Rosetta is a `Django <http://www.djangoproject.com/>`_ application that eases the translation process of your Django projects.

Because it doesn't export any models, Rosetta doesn't create any tables in your project's database. Rosetta can be installed and uninstalled by simply adding and removing a single entry in your project's `INSTALLED_APPS` and a single line in your main ``urls.py`` file.

Note: as of version 0.7.13 django-rosetta requires Django 1.8 or later. As of version 0.9.0, django-rosetta requires Django 1.11 or later.

********
Features
********

* Database independent
* Reads and writes your project's `gettext` catalogs (po and mo files)
* Installed and uninstalled in under a minute
* Uses Django's admin interface CSS


*************
Documentation
*************

Please refer to the `online documentation <http://django-rosetta.readthedocs.org/>`_ to install Rosetta and get started.
