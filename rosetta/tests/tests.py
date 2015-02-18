# -*- coding: utf-8 -*-
from django.conf import settings
from django.contrib.auth.models import User, Group
from django.core.urlresolvers import reverse, resolve
from django.core.exceptions import ImproperlyConfigured
from django.core.cache import cache
from django.template.defaultfilters import floatformat
from django.test import TestCase
from django.test.client import Client
from rosetta.conf import settings as rosetta_settings
from rosetta.signals import entry_changed, post_save
import os
import shutil
import six
import django


try:
    from django.dispatch import receiver
except ImportError:
    # We might be in django < 1.3, so backport this function
    def receiver(signal, **kwargs):
        def _decorator(func):
            signal.connect(func, **kwargs)
            return func
        return _decorator


class RosettaTestCase(TestCase):
    urls = 'rosetta.tests.urls'

    def __init__(self, *args, **kwargs):
        super(RosettaTestCase, self).__init__(*args, **kwargs)
        self.curdir = os.path.dirname(__file__)
        self.dest_file = os.path.normpath(os.path.join(self.curdir, '../locale/xx/LC_MESSAGES/django.po'))
        self.django_version_major, self.django_version_minor = django.VERSION[0], django.VERSION[1]

    def setUp(self):
        user = User.objects.create_user('test_admin', 'test@test.com', 'test_password')
        user2 = User.objects.create_user('test_admin2', 'test@test2.com', 'test_password')
        user3 = User.objects.create_user('test_admin3', 'test@test2.com', 'test_password')

        user.is_superuser, user2.is_superuser, user3.is_superuser = True, True, True
        user.is_staff, user2.is_staff, user3.is_staff = True, True, False

        user.save()
        user2.save()
        user3.save()

        self.client2 = Client()

        self.client.login(username='test_admin', password='test_password')
        self.client2.login(username='test_admin2', password='test_password')

        self.__old_settings_languages = settings.LANGUAGES
        settings.LANGUAGES = (('xx', 'dummy language'), ('fr_FR.utf8', 'French (France), UTF8'))

        self.__session_engine = settings.SESSION_ENGINE
        self.__storage_class = rosetta_settings.STORAGE_CLASS
        self.__require_auth = rosetta_settings.ROSETTA_REQUIRES_AUTH

        shutil.copy(self.dest_file, self.dest_file + '.orig')

    def tearDown(self):
        settings.LANGUAGES = self.__old_settings_languages
        settings.SESSION_ENGINE = self.__session_engine
        rosetta_settings.STORAGE_CLASS = self.__storage_class
        rosetta_settings.ROSETTA_REQUIRES_AUTH = self.__require_auth
        shutil.move(self.dest_file + '.orig', self.dest_file)

    def test_1_ListLoading(self):
        r = self.client.get(reverse('rosetta-pick-file') + '?filter=third-party')
        r = self.client.get(reverse('rosetta-pick-file'))
        self.assertTrue(os.path.normpath('rosetta/locale/xx/LC_MESSAGES/django.po') in str(r.content))

    def test_2_PickFile(self):
        r = self.client.get(reverse('rosetta-pick-file') + '?filter=third-party')
        r = self.client.get(reverse('rosetta-language-selection', args=('xx', 0,), kwargs=dict()) + '?rosetta')
        r = self.client.get(reverse('rosetta-home'))

        self.assertTrue('dummy language' in str(r.content))

    def test_3_DownloadZIP(self):
        r = self.client.get(reverse('rosetta-pick-file') + '?filter=third-party')

        r = self.client.get(reverse('rosetta-language-selection', args=('xx', 0), kwargs=dict()) + '?rosetta')
        r = self.client.get(reverse('rosetta-home'))
        r = self.client.get(reverse('rosetta-download-file') + '?rosetta')
        self.assertTrue('content-type' in r._headers.keys())
        self.assertTrue('application/x-zip' in r._headers.get('content-type'))

    def test_4_DoChanges(self):
        shutil.copy(os.path.normpath(os.path.join(self.curdir, './django.po.template')), self.dest_file)

        # Load the template file
        r = self.client.get(reverse('rosetta-pick-file') + '?filter=third-party')
        r = self.client.get(reverse('rosetta-language-selection', args=('xx', 0), kwargs=dict()))
        r = self.client.get(reverse('rosetta-home') + '?filter=untranslated')
        r = self.client.get(reverse('rosetta-home'))
        # make sure both strings are untranslated
        self.assertTrue('dummy language' in str(r.content))
        self.assertTrue('String 1' in str(r.content))
        self.assertTrue('String 2' in str(r.content))
        self.assertTrue('m_e48f149a8b2e8baa81b816c0edf93890' in str(r.content))

        # post a translation
        r = self.client.post(reverse('rosetta-home'), dict(m_e48f149a8b2e8baa81b816c0edf93890='Hello, world', _next='_next'))

        # reload all untranslated strings
        r = self.client.get(reverse('rosetta-language-selection', args=('xx', 0), kwargs=dict()) + '?rosetta')
        r = self.client.get(reverse('rosetta-home') + '?filter=untranslated')
        r = self.client.get(reverse('rosetta-home'))

        # the translated string no longer is up for translation
        self.assertTrue('String 1'  in str(r.content))
        self.assertTrue('String 2' not in str(r.content))

        # display only translated strings
        r = self.client.get(reverse('rosetta-home') + '?filter=translated')
        r = self.client.get(reverse('rosetta-home'))

        # The tranlsation was persisted
        self.assertTrue('String 1' not  in str(r.content))
        self.assertTrue('String 2' in str(r.content))
        self.assertTrue('Hello, world' in str(r.content))

    def test_5_TestIssue67(self):
        # testcase for issue 67: http://code.google.com/p/django-rosetta/issues/detail?id=67
        shutil.copy(os.path.normpath(os.path.join(self.curdir, './django.po.issue67.template')), self.dest_file)
        # Make sure the plurals string is valid
        f_ = open(self.dest_file, 'rb')
        content = f_.read()
        f_.close()
        self.assertTrue('Hello, world' not in six.text_type(content))
        self.assertTrue('|| n%100>=20) ? 1 : 2)' in six.text_type(content))
        del(content)

        # Load the template file
        r = self.client.get(reverse('rosetta-pick-file') + '?filter=third-party')

        r = self.client.get(reverse('rosetta-language-selection', args=('xx', 0), kwargs=dict()) + '?rosetta')
        r = self.client.get(reverse('rosetta-home') + '?filter=untranslated')
        r = self.client.get(reverse('rosetta-home'))

        # make sure all strings are untranslated
        self.assertTrue('dummy language' in str(r.content))
        self.assertTrue('String 1' in str(r.content))
        self.assertTrue('String 2' in str(r.content))
        self.assertTrue('m_e48f149a8b2e8baa81b816c0edf93890' in str(r.content))

        # post a translation
        r = self.client.post(reverse('rosetta-home'), dict(m_e48f149a8b2e8baa81b816c0edf93890='Hello, world', _next='_next'))

        # Make sure the plurals string is still valid
        f_ = open(self.dest_file, 'rb')
        content = f_.read()
        f_.close()
        self.assertTrue('Hello, world' in str(content))
        self.assertTrue('|| n%100>=20) ? 1 : 2)' in str(content))
        self.assertTrue('or n%100>=20) ? 1 : 2)' not in str(content))
        del(content)

    def test_6_ExcludedApps(self):

        rosetta_settings.EXCLUDED_APPLICATIONS = ('rosetta',)

        r = self.client.get(reverse('rosetta-pick-file') + '?filter=third-party')
        r = self.client.get(reverse('rosetta-pick-file'))
        self.assertTrue('rosetta/locale/xx/LC_MESSAGES/django.po' not in str(r.content))

        rosetta_settings.EXCLUDED_APPLICATIONS = ()

        r = self.client.get(reverse('rosetta-pick-file') + '?rosetta')
        self.assertTrue('rosetta/locale/xx/LC_MESSAGES/django.po' in str(r.content))

    def test_7_selfInApplist(self):
        self.client.get(reverse('rosetta-pick-file') + '?filter=third-party')
        r = self.client.get(reverse('rosetta-pick-file'))
        self.assertTrue('rosetta/locale/xx/LC_MESSAGES/django.po' in str(r.content))

        self.client.get(reverse('rosetta-pick-file') + '?filter=project')
        r = self.client.get(reverse('rosetta-pick-file'))
        self.assertTrue('rosetta/locale/xx/LC_MESSAGES/django.po' not in str(r.content))

    def test_8_showObsoletes(self):
        r = self.client.get(reverse('rosetta-pick-file') + '?filter=third-party')
        r = self.client.get(reverse('rosetta-pick-file'))
        r = self.client.get(reverse('rosetta-language-selection', args=('xx', 0), kwargs=dict()))

        r = self.client.get(reverse('rosetta-home') + '?query=Les%20deux')
        self.assertTrue('dummy language' in str(r.content))
        self.assertTrue('Les deux' in str(r.content))

    def test_9_concurrency(self):
        shutil.copy(os.path.normpath(os.path.join(self.curdir, './django.po.template')), self.dest_file)

        r = self.client.get(reverse('rosetta-pick-file') + '?filter=third-party')
        r = self.client2.get(reverse('rosetta-pick-file') + '?filter=third-party')

        self.client.get(reverse('rosetta-language-selection', args=('xx', 0), kwargs=dict()))
        self.client2.get(reverse('rosetta-language-selection', args=('xx', 0), kwargs=dict()))

        # Load the template file
        r = self.client.get(reverse('rosetta-home') + '?filter=untranslated')
        r = self.client.get(reverse('rosetta-home'))
        r2 = self.client2.get(reverse('rosetta-home') + '?filter=untranslated')
        r2 = self.client2.get(reverse('rosetta-home'))

        self.assertTrue('String 1' in str(r.content))
        self.assertTrue('String 1' in str(r2.content))
        self.assertTrue('m_08e4e11e2243d764fc45a5a4fba5d0f2' in str(r.content))
        r = self.client.post(reverse('rosetta-home'), dict(m_08e4e11e2243d764fc45a5a4fba5d0f2='Hello, world', _next='_next'), follow=True)
        r2 = self.client2.get(reverse('rosetta-home'))

        # Client 2 reloads the home, forces a reload of the catalog,
        # the untranslated string1 is now translated
        self.assertTrue('String 1' not in str(r2.content))
        self.assertTrue('String 2' in str(r2.content))

        r = self.client.get(reverse('rosetta-home') + '?filter=untranslated')
        r = self.client.get(reverse('rosetta-home'))
        r2 = self.client2.get(reverse('rosetta-home') + '?filter=untranslated')
        r2 = self.client2.get(reverse('rosetta-home'))

        self.assertTrue('String 2' in str(r2.content) and 'm_e48f149a8b2e8baa81b816c0edf93890' in str(r2.content))
        self.assertTrue('String 2' in str(r.content) and 'm_e48f149a8b2e8baa81b816c0edf93890' in str(r.content))

        # client 2 posts!
        r2 = self.client2.post(reverse('rosetta-home'), dict(m_e48f149a8b2e8baa81b816c0edf93890='Hello, world, from client two!', _next='_next'), follow=True)

        self.assertTrue('save-conflict' not in str(r2.content))

        # uh-oh here comes client 1
        r = self.client.post(reverse('rosetta-home'), dict(m_e48f149a8b2e8baa81b816c0edf93890='Hello, world, from client one!', _next='_next'), follow=True)
        # An error message is displayed
        self.assertTrue('save-conflict' in str(r.content))

        # client 2 won
        pofile_content = open(self.dest_file, 'r').read()
        self.assertTrue('Hello, world, from client two!' in pofile_content)

        # Both clients show all strings, error messages are gone
        r = self.client.get(reverse('rosetta-home') + '?filter=translated')
        self.assertTrue('save-conflict' not in str(r.content))
        r2 = self.client2.get(reverse('rosetta-home') + '?filter=translated')
        self.assertTrue('save-conflict' not in str(r2.content))
        r = self.client.get(reverse('rosetta-home'))
        self.assertTrue('save-conflict' not in str(r.content))
        r2 = self.client2.get(reverse('rosetta-home'))
        self.assertTrue('save-conflict' not in str(r2.content))

        # Both have client's two version
        self.assertTrue('Hello, world, from client two!' in str(r.content))
        self.assertTrue('Hello, world, from client two!' in str(r2.content))
        self.assertTrue('save-conflict' not in str(r2.content))
        self.assertTrue('save-conflict' not in str(r.content))

    def test_10_issue_79_num_entries(self):
        shutil.copy(os.path.normpath(os.path.join(self.curdir, './django.po.issue79.template')), self.dest_file)
        self.client.get(reverse('rosetta-pick-file') + '?filter=third-party')
        r = self.client.get(reverse('rosetta-pick-file'))

        self.assertTrue('<td class="ch-messages r">1</td>' in str(r.content))
        self.assertTrue('<td class="ch-progress r">%s%%</td>' % str(floatformat(0.0, 2)) in str(r.content))
        self.assertTrue('<td class="ch-obsolete r">1</td>' in str(r.content))

    def test_11_issue_80_tab_indexes(self):
        self.client.get(reverse('rosetta-pick-file') + '?filter=third-party')
        r = self.client.get(reverse('rosetta-language-selection', args=('xx', 0,), kwargs=dict()))
        r = self.client.get(reverse('rosetta-home'))
        self.assertTrue('tabindex="3"' in str(r.content))

    def test_12_issue_82_staff_user(self):
        settings.ROSETTA_REQUIRES_AUTH = True

        self.client3 = Client()
        self.client3.login(username='test_admin3', password='test_password')

        self.client3.get(reverse('rosetta-pick-file') + '?filter=third-party')
        r = self.client3.get(reverse('rosetta-language-selection', args=('xx', 0), kwargs=dict()))
        r = self.client3.get(reverse('rosetta-home'))
        self.assertTrue(not r.content)

        settings.ROSETTA_REQUIRES_AUTH = False

        self.client3.get(reverse('rosetta-pick-file') + '?filter=third-party')
        r = self.client3.get(reverse('rosetta-language-selection', args=('xx', 0,), kwargs=dict()))
        r = self.client3.get(reverse('rosetta-home'))
        self.assertFalse(not r.content)

    def test_13_catalog_filters(self):
        settings.LANGUAGES = (('fr', 'French'), ('xx', 'Dummy Language'),)
        cache.delete('rosetta_django_paths')
        self.client.get(reverse('rosetta-pick-file') + '?filter=third-party')
        r = self.client.get(reverse('rosetta-pick-file'))
        self.assertTrue(os.path.normpath('rosetta/locale/xx/LC_MESSAGES/django.po') in str(r.content))
        self.assertTrue(('contrib') not in str(r.content))

        self.client.get(reverse('rosetta-pick-file') + '?filter=django')
        r = self.client.get(reverse('rosetta-pick-file'))
        self.assertTrue(os.path.normpath('rosetta/locale/xx/LC_MESSAGES/django.po') not in str(r.content))

        if self.django_version_major >= 1 and self.django_version_minor >= 3:
            self.assertTrue(('contrib') in str(r.content))

        self.client.get(reverse('rosetta-pick-file') + '?filter=all')
        r = self.client.get(reverse('rosetta-pick-file'))
        self.assertTrue(os.path.normpath('rosetta/locale/xx/LC_MESSAGES/django.po') in str(r.content))

        if self.django_version_major >= 1 and self.django_version_minor >= 3:
            self.assertTrue(('contrib') in str(r.content))

        self.client.get(reverse('rosetta-pick-file') + '?filter=project')
        r = self.client.get(reverse('rosetta-pick-file'))
        self.assertTrue(os.path.normpath('rosetta/locale/xx/LC_MESSAGES/django.po') not in str(r.content))
        if self.django_version_major >= 1 and self.django_version_minor >= 3:
            self.assertTrue(('contrib') not in str(r.content))

    def test_14_issue_99_context_and_comments(self):
        self.client.get(reverse('rosetta-pick-file') + '?filter=third-party')
        r = self.client.get(reverse('rosetta-language-selection', args=('xx', 0), kwargs=dict()))
        r = self.client.get(reverse('rosetta-home'))
        self.assertTrue('This is a text of the base template' in str(r.content))
        self.assertTrue('Context hint' in str(r.content))

    def test_15_issue_87_entry_changed_signal(self):
        # copy the template file
        shutil.copy(os.path.normpath(os.path.join(self.curdir, './django.po.template')), self.dest_file)

        self.client.get(reverse('rosetta-pick-file') + '?filter=third-party')
        r = self.client.get(reverse('rosetta-language-selection', args=('xx', 0,), kwargs=dict()))
        r = self.client.get(reverse('rosetta-home'))

        @receiver(entry_changed)
        def test_receiver(sender, **kwargs):
            self.test_old_msgstr = kwargs.get('old_msgstr')
            self.test_new_msgstr = sender.msgstr
            self.test_msg_id = sender.msgid
        self.assertTrue('m_e48f149a8b2e8baa81b816c0edf93890' in str(r.content))

        # post a translation
        r = self.client.post(reverse('rosetta-home'), dict(m_e48f149a8b2e8baa81b816c0edf93890='Hello, world', _next='_next'))

        self.assertTrue(self.test_old_msgstr == '')
        self.assertTrue(self.test_new_msgstr == 'Hello, world')
        self.assertTrue(self.test_msg_id == 'String 2')

        del(self.test_old_msgstr, self.test_new_msgstr, self.test_msg_id)

    def test_16_issue_101_post_save_signal(self):
        shutil.copy(os.path.normpath(os.path.join(self.curdir, './django.po.template')), self.dest_file)
        self.client.get(reverse('rosetta-pick-file') + '?filter=third-party')
        r = self.client.get(reverse('rosetta-language-selection', args=('xx', 0), kwargs=dict()))
        r = self.client.get(reverse('rosetta-home'))

        @receiver(post_save)
        def test_receiver(sender, **kwargs):
            self.test_sig_lang = kwargs.get('language_code')

        self.assertTrue('m_e48f149a8b2e8baa81b816c0edf93890' in str(r.content))

        # post a translation
        r = self.client.post(reverse('rosetta-home'), dict(m_e48f149a8b2e8baa81b816c0edf93890='Hello, world', _next='_next'))

        self.assertTrue(self.test_sig_lang == 'xx')
        del(self.test_sig_lang)

    def test_17_issue_103_post_save_signal_has_request(self):
        shutil.copy(os.path.normpath(os.path.join(self.curdir, './django.po.template')), self.dest_file)

        self.client.get(reverse('rosetta-pick-file') + '?filter=third-party')
        r = self.client.get(reverse('rosetta-language-selection', args=('xx', 0), kwargs=dict()))
        r = self.client.get(reverse('rosetta-home'))

        @receiver(post_save)
        def test_receiver(sender, **kwargs):
            self.test_16_has_request = 'request' in kwargs

        self.assertTrue('m_e48f149a8b2e8baa81b816c0edf93890' in str(r.content))

        # post a translation
        r = self.client.post(reverse('rosetta-home'), dict(m_e48f149a8b2e8baa81b816c0edf93890='Hello, world', _next='_next'))

        self.assertTrue(self.test_16_has_request)
        del(self.test_16_has_request)
        # reset the original file

    def test_18_Test_Issue_gh24(self):
        shutil.copy(os.path.normpath(os.path.join(self.curdir, './django.po.issue24gh.template')), self.dest_file)

        self.client.get(reverse('rosetta-pick-file') + '?filter=third-party')
        r = self.client.get(reverse('rosetta-language-selection', args=('xx', 0, ), kwargs=dict()))
        r = self.client.get(reverse('rosetta-home'))

        self.assertTrue('m_bb9d8fe6159187b9ea494c1b313d23d4' in str(r.content))

        # post a translation, it should have properly wrapped lines
        r = self.client.post(reverse('rosetta-home'), dict(m_bb9d8fe6159187b9ea494c1b313d23d4='Lorem ipsum dolor sit amet, consectetuer adipiscing elit. Aenean commodo ligula eget dolor. Aenean massa. Cum sociis natoque penatibus et magnis dis parturient montes, nascetur ridiculus mus. Donec quam felis, ultricies nec, pellentesque eu, pretium quis, sem. Nulla consequat massa quis enim. Donec pede justo, fringilla vel, aliquet nec, vulputate eget, arcu. In enim justo, rhoncus ut, imperdiet a, venenatis vitae, justo. Nullam dictum felis eu pede mollis pretium.', _next='_next'))
        pofile_content = open(self.dest_file, 'r').read()
        self.assertTrue('"pede mollis pretium."' in pofile_content)

        # Again, with unwrapped lines
        shutil.copy(os.path.normpath(os.path.join(self.curdir, './django.po.issue24gh.template')), self.dest_file)
        self.client.get(reverse('rosetta-pick-file') + '?filter=third-party')
        r = self.client.get(reverse('rosetta-language-selection', args=('xx', 0, ), kwargs=dict()))
        r = self.client.get(reverse('rosetta-home'))
        self.assertTrue('m_bb9d8fe6159187b9ea494c1b313d23d4' in str(r.content))
        rosetta_settings.POFILE_WRAP_WIDTH = 0
        r = self.client.post(reverse('rosetta-home'), dict(m_bb9d8fe6159187b9ea494c1b313d23d4='Lorem ipsum dolor sit amet, consectetuer adipiscing elit. Aenean commodo ligula eget dolor. Aenean massa. Cum sociis natoque penatibus et magnis dis parturient montes, nascetur ridiculus mus. Donec quam felis, ultricies nec, pellentesque eu, pretium quis, sem. Nulla consequat massa quis enim. Donec pede justo, fringilla vel, aliquet nec, vulputate eget, arcu. In enim justo, rhoncus ut, imperdiet a, venenatis vitae, justo. Nullam dictum felis eu pede mollis pretium.', _next='_next'))
        pofile_content = open(self.dest_file, 'r').read()
        self.assertTrue('felis eu pede mollis pretium."' in pofile_content)

    def test_19_Test_Issue_gh34(self):
        shutil.copy(os.path.normpath(os.path.join(self.curdir, './django.po.issue34gh.template')), self.dest_file)

        self.client.get(reverse('rosetta-pick-file') + '?filter=third-party')
        r = self.client.get(reverse('rosetta-language-selection', args=('xx', 0, ), kwargs=dict()))
        r = self.client.get(reverse('rosetta-home'))
        self.assertTrue('m_ff7060c1a9aae9c42af4d54ac8551f67_1' in str(r.content))
        self.assertTrue('m_ff7060c1a9aae9c42af4d54ac8551f67_0' in str(r.content))
        self.assertTrue('m_09f7e02f1290be211da707a266f153b3' in str(r.content))

        # post a translation, it should have properly wrapped lines
        r = self.client.post(reverse('rosetta-home'), dict(
            m_ff7060c1a9aae9c42af4d54ac8551f67_0='Foo %s',
            m_ff7060c1a9aae9c42af4d54ac8551f67_1='Bar %s',
            m_09f7e02f1290be211da707a266f153b3='Salut', _next='_next'))
        pofile_content = open(self.dest_file, 'r').read()
        self.assertTrue('msgstr "Salut\\n"' in pofile_content)
        self.assertTrue('msgstr[0] ""\n"\\n"\n"Foo %s\\n"' in pofile_content)
        self.assertTrue('msgstr[1] ""\n"\\n"\n"Bar %s\\n"' in pofile_content)

    def test_20_Test_Issue_gh38(self):
        if self.django_version_minor >= 4 and self.django_version_major >= 1:
            self.assertTrue('django.contrib.sessions.middleware.SessionMiddleware' in settings.MIDDLEWARE_CLASSES)

            settings.SESSION_ENGINE = "django.contrib.sessions.backends.signed_cookies"

            # One: cache backend
            rosetta_settings.STORAGE_CLASS = 'rosetta.storage.CacheRosettaStorage'

            shutil.copy(os.path.normpath(os.path.join(self.curdir, './django.po.issue38gh.template')), self.dest_file)

            self.client.get(reverse('rosetta-pick-file') + '?filter=third-party')
            self.client.get(reverse('rosetta-language-selection', args=('xx', 0, ), kwargs=dict()))
            r = self.client.get(reverse('rosetta-home'))
            self.assertFalse(len(str(self.client.cookies.get('sessionid'))) > 4096)
            self.assertTrue('m_9efd113f7919952523f06e0d88da9c54' in str(r.content))
            r = self.client.post(reverse('rosetta-home'), dict(
                m_9efd113f7919952523f06e0d88da9c54='Testing cookie length',
                _next='_next'
            ))
            pofile_content = open(self.dest_file, 'r').read()
            self.assertTrue('Testing cookie length' in pofile_content)

            self.client.get(reverse('rosetta-home') + '?filter=translated')
            r = self.client.get(reverse('rosetta-home'))
            self.assertTrue('Testing cookie length' in str(r.content))
            self.assertTrue('m_9f6c442c6d579707440ba9dada0fb373' in str(r.content))

            # Two, the cookie backend
            if self.django_version_minor < 6:
                rosetta_settings.STORAGE_CLASS = 'rosetta.storage.SessionRosettaStorage'

                shutil.copy(os.path.normpath(os.path.join(self.curdir, './django.po.issue38gh.template')), self.dest_file)

                self.client.get(reverse('rosetta-pick-file') + '?filter=third-party')
                self.client.get(reverse('rosetta-language-selection', args=('xx', 0, ), kwargs=dict()))
                r = self.client.get(reverse('rosetta-home'))
                self.assertTrue(len(str(self.client.cookies.get('sessionid'))) > 4096)
                # boom: be a good browser, truncate the cookie
                self.client.cookies['sessionid'] = six.text_type(self.client.cookies.get('sessionid'))[:4096]
                r = self.client.get(reverse('rosetta-home'))

                self.assertFalse('m_9efd113f7919952523f06e0d88da9c54' in str(r.content))

    def test_21_concurrency_of_cache_backend(self):
        rosetta_settings.STORAGE_CLASS = 'rosetta.storage.CacheRosettaStorage'
        shutil.copy(os.path.normpath(os.path.join(self.curdir, './django.po.issue38gh.template')), self.dest_file)

        self.client.get(reverse('rosetta-pick-file') + '?filter=third-party')
        self.client.get(reverse('rosetta-language-selection', args=('xx', 0, ), kwargs=dict()))

        self.client2.get(reverse('rosetta-pick-file') + '?filter=third-party')
        self.client2.get(reverse('rosetta-language-selection', args=('xx', 0, ), kwargs=dict()))

        self.assertTrue(self.client.session.get('rosetta_cache_storage_key_prefix') != self.client2.session.get('rosetta_cache_storage_key_prefix'))

    def test_22_Test_Issue_gh39(self):
        shutil.copy(os.path.normpath(os.path.join(self.curdir, './django.po.issue39gh.template')), self.dest_file)

        self.client.get(reverse('rosetta-pick-file') + '?filter=third-party')
        r = self.client.get(reverse('rosetta-language-selection', args=('xx', 0), kwargs=dict()))
        r = self.client.get(reverse('rosetta-home'))
        # We have distinct hashes, even though the msgid and msgstr are identical
        #print (r.content)
        self.assertTrue('m_4765f7de94996d3de5975fa797c3451f' in str(r.content))
        self.assertTrue('m_08e4e11e2243d764fc45a5a4fba5d0f2' in str(r.content))

    def test_23_save_header_data(self):
        shutil.copy(os.path.normpath(os.path.join(self.curdir, './django.po.template')), self.dest_file)

        unicode_user = User.objects.create_user('test_unicode', 'save_header_data@test.com', 'test_unicode')
        unicode_user.first_name = "aéaéaé aàaàaàa"
        unicode_user.last_name = "aâââ üüüü"
        unicode_user.is_superuser, unicode_user.is_staff = True, True
        unicode_user.save()

        self.client.login(username='test_unicode', password='test_unicode')

        # Load the template file
        r = self.client.get(reverse('rosetta-pick-file') + '?filter=third-party')
        r = self.client.get(reverse('rosetta-language-selection', args=('xx', 0), kwargs=dict()))
        r = self.client.get(reverse('rosetta-home') + '?filter=untranslated')
        r = self.client.get(reverse('rosetta-home'))
        # make sure both strings are untranslated
        self.assertTrue('dummy language' in str(r.content))
        self.assertTrue('String 1' in str(r.content))
        self.assertTrue('String 2' in str(r.content))
        self.assertTrue('m_e48f149a8b2e8baa81b816c0edf93890' in str(r.content))

        # post a translation
        r = self.client.post(reverse('rosetta-home'), dict(m_e48f149a8b2e8baa81b816c0edf93890='Hello, world', _next='_next'))
        # read the result
        f_ = open(self.dest_file, 'rb')
        content = six.text_type(f_.read())
        f_.close()
        #print (content)
        # make sure unicode data was properly converted to ascii
        self.assertTrue('Hello, world' in content)
        self.assertTrue('save_header_data@test.com' in content)
        self.assertTrue('aeaeae aaaaaaa aaaa uuuu' in content)

    def test_24_percent_transaltion(self):
        shutil.copy(os.path.normpath(os.path.join(self.curdir, './django.po.template')), self.dest_file)

        # Load the template file
        r = self.client.get(reverse('rosetta-pick-file') + '?filter=third-party')
        r = self.client.get(reverse('rosetta-language-selection', args=('xx', 0), kwargs=dict()))
        r = self.client.get(reverse('rosetta-home') + '?filter=untranslated')
        r = self.client.get(reverse('rosetta-home'))

        self.assertTrue('Progress: 0.00%' in str(r.content))
        r = self.client.post(reverse('rosetta-home'), dict(m_e48f149a8b2e8baa81b816c0edf93890='Hello, world', _next='_next'))
        r = self.client.get(reverse('rosetta-home'))
        self.assertTrue('Progress: 25.00%' in str(r.content))

    def test_25_replace_access_control(self):
        # Test default access control allows access
        url = reverse('rosetta-home')
        response = self.client.get(url)
        self.assertEqual(200, response.status_code)

        # Now replace access control, and check we get redirected
        settings.ROSETTA_ACCESS_CONTROL_FUNCTION = 'rosetta.tests.no_access'
        response = self.client.get(url)
        self.assertEqual(302, response.status_code)

        # Restore setting to default
        settings.ROSETTA_ACCESS_CONTROL_FUNCTION = None

    def test_26_urlconf_accept_dots_and_underscores(self):
        resolver_match = resolve("/rosetta/select/fr_FR.utf8/0/")
        self.assertEqual(resolver_match.url_name, "rosetta-language-selection")
        self.assertEqual(resolver_match.kwargs['langid'], 'fr_FR.utf8')

    def test_27_extended_urlconf_language_code_loads_file(self):
        r = self.client.get(reverse('rosetta-pick-file') + '?filter=all')
        r = self.client.get(reverse('rosetta-language-selection', args=('fr_FR.utf8', 0), kwargs=dict()))
        r = self.client.get(reverse('rosetta-home'))
        self.assertTrue('French (France), UTF8' in str(r.content))
        self.assertTrue('m_71a6479faf8712e37dd5755cd1d11804' in str(r.content))

    def test_28_issue_gh87(self):
        "make sure that rosetta_i18n_catalog_filter is passed into the context"
        r = self.client.get(reverse('rosetta-pick-file') + '?filter=third-party')
        r = self.client.get(reverse('rosetta-pick-file'))
        self.assertTrue('<li class="active"><a href="?filter=third-party">' in str(r.content))

    def test_29_unsupported_p3_django_16_storage(self):
        if self.django_version_minor >= 6 and self.django_version_major >= 1:
            self.assertTrue('django.contrib.sessions.middleware.SessionMiddleware' in settings.MIDDLEWARE_CLASSES)

            settings.SESSION_ENGINE = "django.contrib.sessions.backends.signed_cookies"
            rosetta_settings.STORAGE_CLASS = 'rosetta.storage.SessionRosettaStorage'

            try:
                self.client.get(reverse('rosetta-pick-file') + '?filter=third-party')
                self.fail()
            except ImproperlyConfigured:
                pass

    def test_30_pofile_names(self):
        POFILENAMES = rosetta_settings.POFILENAMES
        rosetta_settings.POFILENAMES = ('pr44.po', )

        os.unlink(self.dest_file)
        destfile = os.path.normpath(os.path.join(self.curdir, '../locale/xx/LC_MESSAGES/pr44.po'))
        shutil.copy(os.path.normpath(os.path.join(self.curdir, './pr44.po.template')), destfile)

        self.client.get(reverse('rosetta-pick-file') + '?filter=third-party')
        r = self.client.get(reverse('rosetta-home'))
        self.assertTrue('xx/LC_MESSAGES/pr44.po' in str(r.content))

        r = self.client.get(reverse('rosetta-language-selection', args=('xx', 0,), kwargs=dict()) + '?rosetta')
        r = self.client.get(reverse('rosetta-home'))

        self.assertTrue('dummy language' in str(r.content))

        os.unlink(destfile)
        rosetta_settings.POFILENAMES = POFILENAMES


    def test_31_pr_102__exclude_paths(self):
        ROSETTA_EXCLUDED_PATHS = rosetta_settings.ROSETTA_EXCLUDED_PATHS

        r = self.client.get(reverse('rosetta-pick-file') + '?filter=third-party')
        r = self.client.get(reverse('rosetta-pick-file'))
        self.assertTrue(os.path.normpath('rosetta/locale/xx/LC_MESSAGES/django.po') in str(r.content))

        exclude_path = os.path.normpath(os.path.join(self.curdir, '../locale'))
        rosetta_settings.ROSETTA_EXCLUDED_PATHS = [exclude_path, ]

        r = self.client.get(reverse('rosetta-pick-file') + '?filter=third-party')
        r = self.client.get(reverse('rosetta-pick-file'))
        self.assertFalse(os.path.normpath('rosetta/locale/xx/LC_MESSAGES/django.po') in str(r.content))

        rosetta_settings.ROSETTA_EXCLUDED_PATHS = ROSETTA_EXCLUDED_PATHS

    def test_32_pr_103__language_groups(self):
        ROSETTA_LANGUAGE_GROUPS = rosetta_settings.ROSETTA_LANGUAGE_GROUPS
        rosetta_settings.ROSETTA_LANGUAGE_GROUPS = False

        # Default behavior: non admins need to be in a translators group, they see
        # all catalogs
        translators = Group.objects.create(name='translators')
        translators_xx = Group.objects.create(name='translators-xx')

        user4 = User.objects.create_user('test_admin4', 'test@test3.com', 'test_password')
        user4.groups.add(translators)
        user4.is_superuser = False
        user4.is_staff = True
        user4.save()
        self.client.login(username='test_admin4', password='test_password')

        r = self.client.get(reverse('rosetta-pick-file') + '?filter=third-party')
        r = self.client.get(reverse('rosetta-pick-file'))
        self.assertTrue(os.path.normpath('rosetta/locale/xx/LC_MESSAGES/django.po') in str(r.content))

        # Activate the option, user doesn't see the XX catalog
        rosetta_settings.ROSETTA_LANGUAGE_GROUPS = True

        r = self.client.get(reverse('rosetta-pick-file') + '?filter=third-party')
        r = self.client.get(reverse('rosetta-pick-file'))
        self.assertFalse(os.path.normpath('rosetta/locale/xx/LC_MESSAGES/django.po') in str(r.content))

        # Now add them to the custom group
        user4.groups.add(translators_xx)

        r = self.client.get(reverse('rosetta-pick-file') + '?filter=third-party')
        r = self.client.get(reverse('rosetta-pick-file'))
        self.assertTrue(os.path.normpath('rosetta/locale/xx/LC_MESSAGES/django.po') in str(r.content))

        rosetta_settings.ROSETTA_LANGUAGE_GROUPS = ROSETTA_LANGUAGE_GROUPS


# Stubbed access control function
def no_access(user):
    return False
