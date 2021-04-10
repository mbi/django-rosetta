==============
Django-Rosetta
==============

.. image:: https://github.com/mbi/django-rosetta/actions/workflows/test.yml/badge.svg
  :target: https://github.com/mbi/django-rosetta/actions/workflows/test.yml

.. image:: https://img.shields.io/pypi/v/django-rosetta
  :target: https://pypi.org/project/django-rosetta/

.. image:: https://img.shields.io/pypi/l/django-rosetta
  :target: https://github.com/mbi/django-rosetta/blob/develop/LICENSE


Rosetta is a `Django <http://www.djangoproject.com/>`_ application that facilitates the translation process of your Django projects.

Because it doesn't export any models, Rosetta doesn't create any tables in your project's database. Rosetta can be installed and uninstalled by simply adding and removing a single entry in your project's `INSTALLED_APPS` and a single line in your main ``urls.py`` file.

Note: as of version 0.9.0, django-rosetta requires Django 1.11 or later, as of version 0.9.6, django-rosetta requires Django 2.2 or later

********
Features
********

* Reads and writes your project's `gettext` catalogs (po and mo files)
* Installed and uninstalled in under a minute
* Uses Django's admin interface CSS

.. image:: https://user-images.githubusercontent.com/131808/104168653-ac277e00-53fe-11eb-975e-8d46551fac59.png


*************
Documentation
*************

Please refer to the `online documentation <http://django-rosetta.readthedocs.org/>`_ to install Rosetta and get started.
