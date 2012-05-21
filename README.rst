=======
Rosetta
=======

This is a fork of the `main project <https://github.com/mbi/django-rosetta/>` optimized with
- better urls
- better performance
- lower memory consumption
- better permissions management
- improved search

Basically it has the same settings, same installation steps and does the same things but better.

************
Requirements
************

Rosetta requires Django 1.3 or later.

Since Google Translation API v1 is deprecated and v2 is available only on paid basis, we use Bing translation API. If you want to enable suggestions with Bing API, add BING_APPID to your settings (check out how to get one here <http://www.microsoft.com/web/post/using-the-free-bing-translation-apis>)

********
Security
********

Because Rosetta requires write access to some of the files in your Django project, access is restricted to the superusers only (as defined in your project's Admin interface)

If you wish to grant somebody access for certain language(s) only:

1. Create a 'translators_<lang_code> group in admin. Eg it would be translators_ru for Russian and translators_ja for Japanese
2. Add user to the created group

Note: membership in 'translators' group grants access to all languages.

