Version History
===============

Version 0.9.8
-------------
* Test against Django 4.0


Version 0.9.7
-------------
* Arabic translation. (#257, thanks @Bashar)
* Translations via the DeepL API (#258, thanks @halitcelik)
* Fixed unicode handling in gettext headers (#259, thanks @NotSqrt)
* Remove six as a dependency
* Move context and comment hints into the right-most column (#260 thanks @jieter)
* Add extra styles block to the base template (#261 thanks @Frohus and @adamjforster)


Version 0.9.6
-------------
* Remove 'providing_args' kwarg from signals instanciation (#250, thanks @mondeja)
* Removed support and tests for Django <= 2.1
* Test against Python 3.9 (#251, thanks @mondeja)
* Upgraded Turkish translation (#253, thanks @realsuayip)
* Added support for Google Translation API  (#222, thanks @martinsvoboda)
* Test against Django 3.2


Version 0.9.5
-------------
* Fixed DeprecationWarning: invalid escape sequence (#234, Thanks @jayvdb)
* Fixed typo in documentation (#232, thanks @timgates42)
* Added Kyrgyz translation (#239,thanks @Soyuzbek)
* Ignore translator context hints checking unmatched variables (#238, #239, thanks @jeancochrane and @mondeja)
* Uncheck fuzzy on translation keyup instead of change (#235 @mondeja)
* Allow passing a function itself to the setting ROSETTA_ACCESS_CONTROL (#227, thanks @alvra)
* Dropped support for Django 1.11 and Python 2
* Test against Django 3.1a
* Do not show Rosetta link in admin panel if user has no access to translations (#240, thanks @mondeja)
* Django 3.1: force #changelist to display:block (#248 thanks @realsuayip and @mondeja)


Version 0.9.4
-------------
* Added ROSETTA_SHOW_OCCURRENCES: Option to hide file name & path (#77, PR #221, thanks @sarathak)
* Unfuzzy fuzzy entries when the translation is changed (#16, PR #220, thanks @sarathak)
* Updated spanish translation (#230, thank you @mondeja)
* Test against Django 3.0 and Python 3.8


Version 0.9.3
-------------
* Added a tooltip to explain fuzzy entries (#206)
* New ROSETTA_LANGUAGES setting allows for translating languages which are not yet in LANGUAGES (#219)
* Fix for duplicate PO files listed on case insensitive filesystems (#47, #52, #218, thanks @malkstar)


Version 0.9.2
-------------
* Cleanup of imports, and use relative imports. Hopefully fixes #209.
* Travis: cleanup and test with Python 3.7


Version 0.9.1
-------------
* Removed old compatibility code for Django < 1.11 (#205, thanks @claudep)
* Allow overriding rosetta login url (#210, thanks @izimobil)
* Test against Django 2.2
* Optional line number in the occurrences column (#215, thanks @pauloxnet)
* Add search in msgctxt (#213, thanks @yakky)
* Strip code tag from Yandex response. (#212, thanks @izimobil)
* Test friendly settings and better tests (#211, thanks @izimobil)
* The reference language didn't work in widows (#189, thanks @pedfercue)


Version 0.9.0
-------------
* Fix `ROSETTA_REQUIRES_AUTH = False` wasn't respected (#203, @BarnabasSzabolcs)
* Django-rosetta now requires Django 1.11 or newer. Rosetta 0.8.3 is the last version to support Django 1.8 through 1.10. (#204, thanks @claudep)


Version 0.8.3
-------------
* Replace the (no longer working) Microsoft translation API with the new Azure Translator API (Fixes #200 and #201, thank you @svdvonde)


Version 0.8.2
-------------
* Avoid UnicodeEncodeError when quering strings (#197, thanks @YAtOff)
* Test against Django 2.1


Version 0.8.1
-------------
* PR #194, thanks again @jbaldivieso!

  * Allow searching for plural strings, both in the original and translation. (Fixes #186)
  * HTML-encoding ampersands in the template (minor regression introduced with 0.8.0)
  * Stop showing "None" in the search input if there was no search query submitted

Version 0.8.0
--------------
* PR #194, huge thanks to @jbaldivieso:

  * Better, cleaner RESTful URLs
  * Massive rewrite of Rosetta's view functions as CBVs
  * Better management of cached content

* Check for PEP8 validity during tests

Version 0.7.14
--------------
* Updated installation docs (PR #190, thanks @AuHau)
* Test against Django 2.0


Version 0.7.13
--------------
* Search in comments, too (PR #174, thanks @torchingloom)
* Added `ROSETTA_SHOW_AT_ADMIN_PANEL` setting to display add a link to Rosetta from the admin app index page. (PR #176, thanks @scream4ik)
* Test against Django 1.11
* Template cleanup (Issue #181, thanks @Ecno92)


Version 0.7.12
--------------
* Fix IndexError in fix_nls when translation is just a carriage return (PR #168, thanks @nealtodd)
* Remove float formatting of integer percent translated (PR #171, thanks @nealtodd)
* Fixed a comment (PR #170, thanks @dnaranjo89)
* Test against Django 1.10
* Dropped support for goslate and the Google translate API


Version 0.7.11
--------------
* Make MO file compilation optional (PR #166, Issue #155, thanks @nealtodd)
* Fix an invalid page get parameter by falling back to page 1 (PR #165, thanks @nealtodd)
* Adds reference language selector (PR #60, thanks @hsoft)

Version 0.7.10
--------------
* Re-released 0.7.9 to include a missing image (Issue #162, thanks @legios89)

Version 0.7.9
-------------
* Use language code without country specification for Yandex dest lang (PR #152, thanks @nealtodd)
* Support discovering locale directories like zh_Hans(xx_Xxxx) (Fixes #133 via PR #153 and #133, thanks @glasslion and @dohsimpson)
* Ship Django's original search icon as a static asset (Fixes #157, thanks @facconi)
* Added a warning about translation via the Google Translate service being deprecated in the next version


Version 0.7.8
-------------
* Adds missing includes in MANIFEST.in
* Support for running tests via setuptools
* Updated microsofttranslator dependency version

Version 0.7.7
-------------
* Supported Django versions are now 1.7, 1.8 and 1.9
* Added proper documentation
* Fixed typo in documentation (PR #130, thanks @dfrdmn)
* Fixes the Fuzzy toggle link by adding an actual toggle checkbox (Issue #132, thanks @EmilStenstrom)
* Better handling of Custom User Models while checking wether the current User is authorized to translate (Issue #131, thanks @EmilStenstrom)
* Include the testproject in the sdist tarball to allow Debian to run tests during installation (Issue #137, thanks @fladi)
* Display an explicit error message to the enduser when saving the POfile fails for some reason (Issue #135, thanks @pgcd)
* Added support for PEP 3101 string formatting (PR #140, thanks @adamjforster)
* Added support for composite locales, e.g. 'bs-Cyrl-BA' (Issue #142, thanks @felarov)
* Fixed a misplaced CSRF token (PR #145, thanks @pajod)


Version 0.7.6
-------------
* Added support for the Free Google Translate API (PR #117, thanks @cuchac)
* Probable fix for apps defined by their AppConfig causing havoc in Django 1.7 and later (Issues #113 and #125)
* Test configuration improved to test against Django 1.8 beta 1 and Django 1.7.5
* Require polib >= 1.0.6 (PR #127, thanks @NotSqrt)
* Test against Django 1.8 final


Version 0.7.5
-------------
* Fixed external JavaScript import to be url scheme independent (PR #101, thanks @tsouvarev)
* Fixed a test
* Added support for excluding certain locale paths from the list of PO catalogs (PR #102, thanks @elpaso)
* Added support for translator groups (PR #103, thanks @barklund)
* Removed Microsoft Translator as a shipped lib, relying on an external version instead
* Improved the app loading mechanism to cope with Django 1.7's new AppConfig (thanks @artscoop)
* Fixed a couple inconsistencies in the German translation. (thanks @benebun)
* Use content_type instead of mimetype in HttpResponse. (Issue #115, thanks @vesteinn)
* Don't assume that request.user has settable properties, this was a silly idea anyway (Issue #114, thanks @stevejalim)
* Preserve HTML code when receiving translations from the Yandex translation service (Issue #116, thanks @marcbelmont)
* Use TOX for testing
* Test against Django 1.8a


Version 0.7.4
-------------
* New ROSETTA_POFILENAMES setting. (PR #44, thanks @wrboyce)
* Updated Czech translation (#97, #99 thanks @cuchac)
* Fixed gettext standard compliance of all shipped translations
* No longer ship polib, rely on the Cheeseshop instead


Version 0.7.3
-------------
* Fix for test settings leaking onto global settings: LANGUAGES was overridden and not set back (Issue #81 - Thanks @zsoldosp)
* Test against Django 1.6.1
* Missing context variable in catalog list (Issue #87 - Thanks @kunitoki)
* Added support for Yandex translation API (Issue #89 - Thanks @BlackWizard) See supported languages and limitations here: https://github.com/mbi/django-rosetta/pull/89
* Added support for the Azure translation API, replacing the BING API. (Issue #86, thanks @davidkuchar and @maikelwever)
* Removed support for the signed_cookies SESSION_ENGINE + SessionRosettaStorage in Django 1.6, because serialization of POFiles would fail
* Simplified the group membership test (Issue #90 - Thanks @dotsbb)
* Better serving of admin static files. (Issue #61, thanks @tback)
* Dropped Django 1.3 support


Version 0.7.2
-------------
* Fix for when settings imports unicode_literals for some reason (Issue #67)
* Fixed mess with app_id between pages (Issue #68, thanks @tsouvarev)
* Added Farsi translation. Thanks, @amiraliakbari
* Improved the permission system, allowing for more advanced permission mechanisms. Thanks, @codeinthehole and @tangentlabs
* Fixed the ordering of apps in the language selection screen. (Issue #73, thanks @tsouvarev, @kanu and everyone else involved in tracking this one down)
* Support for complex locale names. (Issue #71, Thanks @strycore)
* Configurable cache name (Issue #75, Thanks @Karmak23)

Version 0.7.1
-------------
* Fix: value missing in context

Version 0.7.0
-------------
* Support for Django 1.5 and HEAD, support for Python 3.
* Upgraded bundled polib to version 1.0.3 - http://pypi.python.org/pypi/polib/1.0.3
* Support timezones on the last modified PO header. Thanks @jmoiron (Issue #43)
* Actually move to the next block when submitting a lot of translations (Issue #13)
* Add msgctxt to the entry hash to differentiate entries with context. Thanks @metalpriest (Issue #39)
* Better discovery of locale files on Django 1.4+ Thanks @tijs (Issues #63, #64)
* List apps in alphabetical order

Version 0.6.8
-------------
* Switched to a pluggable storage backend model to increase compatibility with Django 1.4. Cache and Session-based storages are provided.

Version 0.6.7
-------------
* Added a testproject to run tests
* Updated french translation. Thanks, @BertrandBordage
* Merged @sleepyjames' PR that fixes an error when pofile save path contains '.po' in the path
* Merged @rory's PR to correcty handle plural strings that have a leading/trailing newline (Issue #34)

Version 0.6.6
-------------
* Django 1.4 support (Issue #30, #33)
* Better handling of translation callbacks on Bing's translation API and support of composite locales (Issue #26)

Version 0.6.5
-------------
* Updated polib to 0.7.0
* Added ROSETTA_POFILE_WRAP_WIDTH setting to track the line-length of the updated Po file. (Issue #24)
* Renamed the ``messages``context variable to ``rosetta_messages`` prevent conflicts with ``django.contrib.messages`` (Issue #23)

Version 0.6.4
-------------
* Added ROSETTA_REQUIRES_AUTH option to grant access to non authenticated users (False by default)

Version 0.6.3
-------------
* Support for the Bing transation API service to replace Google's service which is no longer free.
