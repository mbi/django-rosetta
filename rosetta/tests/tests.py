import filecmp
import hashlib
import os
import shutil
from urllib.parse import urlencode

import vcr
from django import VERSION
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.dispatch import receiver
from django.http import Http404
from django.test import RequestFactory, TestCase, override_settings
from django.test.client import Client
from django.urls import resolve, reverse
from django.utils.encoding import force_bytes
from rosetta import views
from rosetta.signals import entry_changed, post_save
from rosetta.storage import get_storage


class RosettaTestCase(TestCase):
    def __init__(self, *args, **kwargs):
        super(RosettaTestCase, self).__init__(*args, **kwargs)
        self.curdir = os.path.dirname(__file__)
        self.dest_file = os.path.normpath(
            os.path.join(self.curdir, '../locale/xx/LC_MESSAGES/django.po')
        )

    def setUp(self):
        from django.contrib.auth.models import User

        user = User.objects.create_superuser(
            'test_admin', 'test@test.com', 'test_password'
        )
        user2 = User.objects.create_superuser(
            'test_admin2', 'test@test2.com', 'test_password'
        )
        user3 = User.objects.create_superuser(
            'test_admin3', 'test@test2.com', 'test_password'
        )

        user3.is_staff = False
        user3.save()

        self.user = user
        self.client2 = Client()

        self.client.login(username=user.username, password='test_password')
        self.client2.login(username=user2.username, password='test_password')

        shutil.copy(self.dest_file, self.dest_file + '.orig')

    def tearDown(self):
        shutil.move(self.dest_file + '.orig', self.dest_file)

    def copy_po_file_from_template(self, template_path):
        """Utility method to handle swapping a template po file in place for
        testing.
        """
        src_path = os.path.normpath(os.path.join(self.curdir, template_path))
        shutil.copy(src_path, self.dest_file)

    @property
    def xx_form_url(self):
        kwargs = {'po_filter': 'third-party', 'lang_id': 'xx', 'idx': 0}
        return reverse('rosetta-form', kwargs=kwargs)

    @property
    def all_file_list_url(self):
        return reverse('rosetta-file-list', kwargs={'po_filter': 'all'})

    @property
    def project_file_list_url(self):
        return reverse('rosetta-file-list', kwargs={'po_filter': 'project'})

    @property
    def third_party_file_list_url(self):
        return reverse('rosetta-file-list', kwargs={'po_filter': 'third-party'})

    def test_1_ListLoading(self):
        r = self.client.get(self.third_party_file_list_url)
        self.assertTrue(
            os.path.normpath('rosetta/locale/xx/LC_MESSAGES/django.po')
            in r.content.decode()
        )

    @override_settings(ROSETTA_LANGUAGES=(('xx', 'dummy language'),))
    def test_2_PickFile(self):
        r = self.client.get(self.xx_form_url)
        self.assertTrue('dummy language' in r.content.decode())

    def test_3_DownloadZIP(self):
        kwargs = {'po_filter': 'third-party', 'lang_id': 'xx', 'idx': 0}
        url = reverse('rosetta-download-file', kwargs=kwargs)
        r = self.client.get(url)
        self.assertTrue('application/x-zip' in r['content-type'])

    @override_settings(ROSETTA_LANGUAGES=(('xx', 'dummy language'),))
    def test_4_DoChanges(self):
        self.copy_po_file_from_template('./django.po.template')
        untranslated_url = self.xx_form_url + '?msg_filter=untranslated'
        translated_url = self.xx_form_url + '?msg_filter=translated'

        # Load the template file
        r = self.client.get(untranslated_url)

        # make sure both strings are untranslated
        self.assertTrue('dummy language' in r.content.decode())
        self.assertTrue('String 1' in r.content.decode())
        self.assertTrue('String 2' in r.content.decode())
        self.assertTrue('m_e48f149a8b2e8baa81b816c0edf93890' in r.content.decode())

        # post a translation
        data = {'m_e48f149a8b2e8baa81b816c0edf93890': 'Hello, world'}
        r = self.client.post(untranslated_url, data, follow=True)

        # reload all untranslated strings
        r = self.client.get(untranslated_url)

        # the translated string no longer is up for translation
        self.assertTrue('String 1' in r.content.decode())
        self.assertTrue('String 2' not in r.content.decode())

        # display only translated strings
        r = self.client.get(translated_url)

        # The translation was persisted
        self.assertTrue('String 1' not in r.content.decode())
        self.assertTrue('String 2' in r.content.decode())
        self.assertTrue('Hello, world' in r.content.decode())

    @override_settings(ROSETTA_LANGUAGES=(('xx', 'dummy language'),))
    def test_5_TestIssue67(self):
        # issue 67: http://code.google.com/p/django-rosetta/issues/detail?id=67
        self.copy_po_file_from_template('./django.po.issue67.template')

        # Make sure the plurals string is valid
        with open(self.dest_file, 'r') as f_:
            content = f_.read()
        self.assertTrue('Hello, world' not in content)
        self.assertTrue('|| n%100>=20) ? 1 : 2)' in content)
        del content

        r = self.client.get(self.xx_form_url + '?msg_filter=untranslated')

        # make sure all strings are untranslated
        self.assertTrue('dummy language' in r.content.decode())
        self.assertTrue('String 1' in r.content.decode())
        self.assertTrue('String 2' in r.content.decode())
        self.assertTrue('m_e48f149a8b2e8baa81b816c0edf93890' in r.content.decode())

        # post a translation
        data = {'m_e48f149a8b2e8baa81b816c0edf93890': 'Hello, world'}
        self.client.post(self.xx_form_url + '?msg_filter=untranslated', data)

        # Make sure the plurals string is still valid
        with open(self.dest_file, 'r') as f_:
            content = f_.read()
        self.assertTrue('Hello, world' in str(content))
        self.assertTrue('|| n%100>=20) ? 1 : 2)' in str(content))
        self.assertTrue('or n%100>=20) ? 1 : 2)' not in str(content))
        del content

    @override_settings(ROSETTA_LANGUAGES=(('xx', 'dummy language'),))
    def test_6_ExcludedApps(self):
        with self.settings(ROSETTA_EXCLUDED_APPLICATIONS=('rosetta',)):
            r = self.client.get(self.third_party_file_list_url)
            self.assertNotContains(r, 'rosetta/locale/xx/LC_MESSAGES/django.po')

        with self.settings(ROSETTA_EXCLUDED_APPLICATIONS=()):
            r = self.client.get(self.third_party_file_list_url)
            self.assertContains(r, 'rosetta/locale/xx/LC_MESSAGES/django.po')

    def test_7_selfInApplist(self):
        r = self.client.get(self.third_party_file_list_url)
        self.assertContains(r, 'rosetta/locale/xx/LC_MESSAGES/django.po')

        r = self.client.get(self.project_file_list_url)
        self.assertNotContains(r, 'rosetta/locale/xx/LC_MESSAGES/django.po')

    @override_settings(ROSETTA_LANGUAGES=(('xx', 'dummy language'),))
    def test_8_hideObsoletes(self):
        r = self.client.get(self.xx_form_url)

        # not in listing
        for p in range(1, 5):
            r = self.client.get(self.xx_form_url + '?page=%d' % p)
            self.assertTrue('dummy language' in r.content.decode())
            self.assertTrue('Les deux' not in r.content.decode())

        r = self.client.get(self.xx_form_url + '?query=Les%20Deux')
        self.assertContains(r, 'dummy language')
        self.assertNotContains(r, 'Les deux')

    def test_9_concurrency(self):
        self.copy_po_file_from_template('./django.po.template')
        translated_url = self.xx_form_url + '?msg_filter=translated'
        untranslated_url = self.xx_form_url + '?msg_filter=untranslated'

        # Load the template file
        r = self.client.get(untranslated_url)
        r2 = self.client2.get(untranslated_url)

        self.assertContains(r, 'String 1')
        self.assertContains(r2, 'String 1')
        self.assertContains(r, 'm_08e4e11e2243d764fc45a5a4fba5d0f2')

        data = {'m_08e4e11e2243d764fc45a5a4fba5d0f2': 'Hello, world'}
        r = self.client.post(untranslated_url, data, follow=True)

        # Client 2 reloads, forces a reload of the catalog; untranslated
        # string1 is now translated
        r2 = self.client2.get(untranslated_url, follow=True)
        self.assertNotContains(r, 'String 1')
        self.assertContains(r, 'String 2')
        self.assertNotContains(r2, 'String 1')
        self.assertContains(r2, 'String 2')

        r = self.client.get(untranslated_url)
        r2 = self.client2.get(untranslated_url)

        self.assertContains(r2, 'String 2')
        self.assertContains(r2, 'm_e48f149a8b2e8baa81b816c0edf93890')
        self.assertContains(r, 'String 2')
        self.assertContains(r, 'm_e48f149a8b2e8baa81b816c0edf93890')

        # client 2 posts!
        data = {'m_e48f149a8b2e8baa81b816c0edf93890': 'Hello, world, from client two!'}
        r2 = self.client2.post(untranslated_url, data, follow=True)

        self.assertNotContains(r2, 'save-conflict')

        # uh-oh here comes client 1
        data = {'m_e48f149a8b2e8baa81b816c0edf93890': 'Hello, world, from client one!'}
        r = self.client.post(untranslated_url, data, follow=True)
        # An error message is displayed
        self.assertContains(r, 'save-conflict')

        # client 2 won
        with open(self.dest_file, 'r') as po_file:
            pofile_content = po_file.read()
        self.assertTrue('Hello, world, from client two!' in pofile_content)

        # Both clients show all strings, error messages are gone
        r = self.client.get(translated_url)
        self.assertNotContains(r, 'save-conflict')
        r2 = self.client2.get(translated_url)
        self.assertNotContains(r2, 'save-conflict')
        r = self.client.get(self.xx_form_url)
        self.assertNotContains(r, 'save-conflict')
        r2 = self.client2.get(self.xx_form_url)
        self.assertNotContains(r2, 'save-conflict')

        # Both have client's two version
        self.assertContains(r, 'Hello, world, from client two!')
        self.assertContains(r2, 'Hello, world, from client two!')

    def test_10_issue_79_num_entries(self):
        self.copy_po_file_from_template('./django.po.issue79.template')
        r = self.client.get(self.third_party_file_list_url)
        self.assertContains(r, '<td class="ch-messages r">1</td>')
        self.assertContains(r, '<td class="ch-progress r">0%</td>')
        self.assertContains(r, '<td class="ch-obsolete r">1</td>')

    def test_11_issue_80_tab_indexes(self):
        r = self.client.get(self.xx_form_url)
        self.assertTrue('tabindex="3"' in r.content.decode())

    def test_12_issue_82_staff_user(self):
        self.client3 = Client()
        self.client3.login(username='test_admin3', password='test_password')

        # When auth is required, we get an empty response (and a redirect) with
        # this user.
        with self.settings(ROSETTA_REQUIRES_AUTH=True):
            r = self.client3.get(self.xx_form_url)
            self.assertFalse(r.content.decode())
            self.assertEqual(r.status_code, 302)

        # When it's not required, we sail through.
        with self.settings(ROSETTA_REQUIRES_AUTH=False):
            r = self.client3.get(self.xx_form_url)
            self.assertTrue(r.content.decode())
            self.assertEqual(r.status_code, 200)

    @override_settings(ROSETTA_LANGUAGES=(('fr', 'French'), ('xx', 'Dummy Language')))
    def test_13_catalog_filters(self):
        r = self.client.get(self.third_party_file_list_url)
        self.assertTrue(
            os.path.normpath('rosetta/locale/xx/LC_MESSAGES/django.po')
            in r.content.decode()
        )

        url = reverse('rosetta-file-list', kwargs={'po_filter': 'django'})
        r = self.client.get(url)
        self.assertTrue(
            os.path.normpath('rosetta/locale/xx/LC_MESSAGES/django.po')
            not in r.content.decode()
        )

        r = self.client.get(self.all_file_list_url)
        self.assertTrue(
            os.path.normpath('rosetta/locale/xx/LC_MESSAGES/django.po')
            in r.content.decode()
        )

        r = self.client.get(self.project_file_list_url)
        self.assertTrue(
            os.path.normpath('rosetta/locale/xx/LC_MESSAGES/django.po')
            not in r.content.decode()
        )

    def test_14_issue_99_context_and_comments(self):
        r = self.client.get(self.xx_form_url)
        self.assertTrue('This is a text of the base template' in r.content.decode())
        self.assertTrue('Context hint' in r.content.decode())

    def test_15_issue_87_entry_changed_signal(self):
        self.copy_po_file_from_template('./django.po.template')
        r = self.client.get(self.xx_form_url)

        @receiver(entry_changed)
        def test_receiver(sender, **kwargs):
            self.test_old_msgstr = kwargs.get('old_msgstr')
            self.test_new_msgstr = sender.msgstr
            self.test_msg_id = sender.msgid

        self.assertTrue('m_e48f149a8b2e8baa81b816c0edf93890' in r.content.decode())

        # post a translation
        data = {'m_e48f149a8b2e8baa81b816c0edf93890': 'Hello, world'}
        self.client.post(self.xx_form_url, data)

        self.assertTrue(self.test_old_msgstr == '')
        self.assertTrue(self.test_new_msgstr == 'Hello, world')
        self.assertTrue(self.test_msg_id == 'String 2')

        del (self.test_old_msgstr, self.test_new_msgstr, self.test_msg_id)

    def test_16_issue_101_post_save_signal(self):
        self.copy_po_file_from_template('./django.po.template')
        r = self.client.get(self.xx_form_url)

        @receiver(post_save)
        def test_receiver(sender, **kwargs):
            self.test_sig_lang = kwargs.get('language_code')

        self.assertTrue('m_e48f149a8b2e8baa81b816c0edf93890' in r.content.decode())

        # post a translation
        data = {'m_e48f149a8b2e8baa81b816c0edf93890': 'Hello, world'}
        self.client.post(self.xx_form_url, data)

        self.assertTrue(self.test_sig_lang == 'xx')
        del self.test_sig_lang

    def test_17_issue_103_post_save_signal_has_request(self):
        self.copy_po_file_from_template('./django.po.template')
        r = self.client.get(self.xx_form_url)

        @receiver(post_save)
        def test_receiver(sender, **kwargs):
            self.test_16_has_request = 'request' in kwargs

        self.assertTrue('m_e48f149a8b2e8baa81b816c0edf93890' in r.content.decode())

        # post a translation
        data = {'m_e48f149a8b2e8baa81b816c0edf93890': 'Hello, world'}
        r = self.client.post(self.xx_form_url, data)

        self.assertTrue(self.test_16_has_request)
        del self.test_16_has_request

    def test_18_Test_Issue_gh24(self):
        self.copy_po_file_from_template('./django.po.issue24gh.template')
        r = self.client.get(self.xx_form_url)

        self.assertTrue('m_bb9d8fe6159187b9ea494c1b313d23d4' in r.content.decode())

        # Post a translation, it should have properly wrapped lines
        data = {
            'm_bb9d8fe6159187b9ea494c1b313d23d4': 'Lorem ipsum dolor sit amet, consectetuer adipiscing elit. Aenean '
            'commodo ligula eget dolor. Aenean massa. Cum sociis natoque '
            'penatibus et magnis dis parturient montes, nascetur ridiculus '
            'mus. Donec quam felis, ultricies nec, pellentesque eu, pretium '
            'quis, sem. Nulla consequat massa quis enim. Donec pede justo, '
            'fringilla vel, aliquet nec, vulputate eget, arcu. In enim justo, '
            'rhoncus ut, imperdiet a, venenatis vitae, justo. Nullam dictum '
            'felis eu pede mollis pretium.'
        }
        r = self.client.post(self.xx_form_url, data)
        with open(self.dest_file, 'r') as po_file:
            pofile_content = po_file.read()

        self.assertTrue('"pede mollis pretium."' in pofile_content)

        # Again, with unwrapped lines
        self.copy_po_file_from_template('./django.po.issue24gh.template')
        with self.settings(ROSETTA_POFILE_WRAP_WIDTH=0):
            r = self.client.get(self.xx_form_url)
            self.assertTrue('m_bb9d8fe6159187b9ea494c1b313d23d4' in r.content.decode())
            r = self.client.post(self.xx_form_url, data)
            with open(self.dest_file, 'r') as po_file:
                pofile_content = po_file.read()
            self.assertTrue('felis eu pede mollis pretium."' in pofile_content)

    def test_19_Test_Issue_gh34(self):
        self.copy_po_file_from_template('./django.po.issue34gh.template')
        r = self.client.get(self.xx_form_url)
        self.assertTrue('m_ff7060c1a9aae9c42af4d54ac8551f67_1' in r.content.decode())
        self.assertTrue('m_ff7060c1a9aae9c42af4d54ac8551f67_0' in r.content.decode())
        self.assertTrue('m_09f7e02f1290be211da707a266f153b3' in r.content.decode())

        # post a translation, it should have properly wrapped lines
        data = {
            'm_ff7060c1a9aae9c42af4d54ac8551f67_0': 'Foo %s',
            'm_ff7060c1a9aae9c42af4d54ac8551f67_1': 'Bar %s',
            'm_09f7e02f1290be211da707a266f153b3': 'Salut',
        }
        r = self.client.post(self.xx_form_url, data)
        with open(self.dest_file, 'r') as po_file:
            pofile_content = po_file.read()
        self.assertTrue('msgstr "Salut\\n"' in pofile_content)
        self.assertTrue('msgstr[0] ""\n"\\n"\n"Foo %s\\n"' in pofile_content)
        self.assertTrue('msgstr[1] ""\n"\\n"\n"Bar %s\\n"' in pofile_content)

    @override_settings(
        SESSION_ENGINE='django.contrib.sessions.backends.signed_cookies',
        ROSETTA_STORAGE_CLASS='rosetta.storage.CacheRosettaStorage',
    )
    def test_20_Test_Issue_gh38(self):
        # (Have to log in again, since our session engine changed)
        self.client.login(username='test_admin', password='test_password')
        self.assertTrue(
            'django.contrib.sessions.middleware.SessionMiddleware' in settings.MIDDLEWARE
        )

        # Only one backend to test: cache backend
        self.copy_po_file_from_template('./django.po.issue38gh.template')

        r = self.client.get(self.xx_form_url)
        self.assertFalse(len(str(self.client.cookies.get('sessionid'))) > 4096)
        self.assertTrue('m_9efd113f7919952523f06e0d88da9c54' in r.content.decode())

        data = {'m_9efd113f7919952523f06e0d88da9c54': 'Testing cookie length'}
        r = self.client.post(self.xx_form_url, data)
        with open(self.dest_file, 'r') as po_file:
            pofile_content = po_file.read()
        self.assertTrue('Testing cookie length' in pofile_content)

        r = self.client.get(self.xx_form_url + '?filter=translated')
        self.assertTrue('Testing cookie length' in r.content.decode())
        self.assertTrue('m_9f6c442c6d579707440ba9dada0fb373' in r.content.decode())

    @override_settings(ROSETTA_STORAGE_CLASS='rosetta.storage.CacheRosettaStorage')
    def test_21_concurrency_of_cache_backend(self):
        self.copy_po_file_from_template('./django.po.issue38gh.template')

        # Force caching into play by making .po file read-only
        os.chmod(self.dest_file, 292)  # 0444

        self.client.get(self.xx_form_url)
        self.client2.get(self.xx_form_url)
        self.assertNotEqual(
            self.client.session.get('rosetta_cache_storage_key_prefix'),
            self.client2.session.get('rosetta_cache_storage_key_prefix'),
        )

        # Clean up (restore perms)
        os.chmod(self.dest_file, 420)  # 0644

    def test_22_Test_Issue_gh39(self):
        self.copy_po_file_from_template('./django.po.issue39gh.template')

        r = self.client.get(self.xx_form_url)
        # We have distinct hashes, even though the msgid and msgstr are identical
        self.assertTrue('m_4765f7de94996d3de5975fa797c3451f' in r.content.decode())
        self.assertTrue('m_08e4e11e2243d764fc45a5a4fba5d0f2' in r.content.decode())

    @override_settings(ROSETTA_LANGUAGES=(('xx', 'dummy language'),))
    def test_23_save_header_data(self):
        from django.contrib.auth.models import User

        self.copy_po_file_from_template('./django.po.template')

        unicode_user = User.objects.create_user(
            'test_unicode', 'save_header_data@test.com', 'test_unicode'
        )
        unicode_user.first_name = "aéaéaé aàaàaàa"
        unicode_user.last_name = "aâââ üüüü"
        unicode_user.is_superuser, unicode_user.is_staff = True, True
        unicode_user.save()

        self.client.login(username='test_unicode', password='test_unicode')

        # Load the template file
        r = self.client.get(self.xx_form_url + '?filter=untranslated')

        # make sure both strings are untranslated
        self.assertTrue('dummy language' in r.content.decode())
        self.assertTrue('String 1' in r.content.decode())
        self.assertTrue('String 2' in r.content.decode())
        self.assertTrue('m_e48f149a8b2e8baa81b816c0edf93890' in r.content.decode())

        # post a translation
        data = {'m_e48f149a8b2e8baa81b816c0edf93890': 'Hello, world'}
        r = self.client.post(self.xx_form_url + '?filter=untranslated', data)
        # read the result
        with open(self.dest_file, 'r') as f_:
            content = f_.read()

        # make sure unicode data was properly converted to ascii
        self.assertTrue('Hello, world' in content)
        self.assertTrue('save_header_data@test.com' in content)
        self.assertTrue('aéaéaé aàaàaàa aâââ üüüü' in content)

    def test_24_percent_translation(self):
        self.copy_po_file_from_template('./django.po.template')

        # Load the template file
        r = self.client.get(self.xx_form_url)

        self.assertTrue('Progress: 0%' in r.content.decode())
        data = {'m_e48f149a8b2e8baa81b816c0edf93890': 'Hello, world'}
        r = self.client.post(self.xx_form_url, data, follow=True)
        self.assertTrue('Progress: 25%' in r.content.decode())

    def test_25_replace_access_control(self):
        # Test default access control allows access
        response = self.client.get(self.project_file_list_url)
        self.assertEqual(200, response.status_code)

        # Now replace access control with a function reference,
        # and check we get redirected
        with self.settings(ROSETTA_ACCESS_CONTROL_FUNCTION='rosetta.tests.no_access'):
            response = self.client.get(self.project_file_list_url)
            self.assertEqual(302, response.status_code)

        # Now replace access control with a function itself,
        # and check we get redirected
        with self.settings(ROSETTA_ACCESS_CONTROL_FUNCTION=lambda user: False):
            response = self.client.get(self.project_file_list_url)
            self.assertEqual(302, response.status_code)

    def test_26_urlconf_accept_dots_and_underscores(self):
        resolver_match = resolve('/rosetta/files/all/fr_FR.utf8/0/')
        self.assertEqual(resolver_match.url_name, 'rosetta-form')
        self.assertEqual(resolver_match.kwargs['lang_id'], 'fr_FR.utf8')

    def test_27_extended_urlconf_language_code_loads_file(self):
        url = reverse(
            'rosetta-form', kwargs={'po_filter': 'all', 'lang_id': 'fr_FR.utf8', 'idx': 0}
        )
        r = self.client.get(url)
        self.assertTrue('French (France), UTF8' in r.content.decode())
        self.assertTrue('m_03a603523bd75b00414a413657acdeb2' in r.content.decode())

    def test_28_issue_gh87(self):
        """Make sure that rosetta_i18n_catalog_filter is passed into the context."""
        r = self.client.get(self.third_party_file_list_url)
        self.assertContains(
            r, '<li class="active"><a href="/rosetta/files/third-party/">'
        )

    @override_settings(
        SESSION_ENGINE='django.contrib.sessions.backends.signed_cookies',
        ROSETTA_STORAGE_CLASS='rosetta.storage.SessionRosettaStorage',
    )
    def test_29_unsupported_p3_django_16_storage(self):
        if VERSION[0:2] < (2, 0):
            self.assertTrue(
                'django.contrib.sessions.middleware.SessionMiddleware'
                in settings.MIDDLEWARE
            )

            # Force caching to be used by making the pofile read-only
            os.chmod(self.dest_file, 292)  # 0444

            # (Have to log in again, since our session engine changed)
            self.client.login(username='test_admin', password='test_password')

            with self.assertRaises(ImproperlyConfigured):
                self.client.get(self.xx_form_url)

            # Cleanup
            os.chmod(self.dest_file, 420)  # 0644

    @override_settings(
        ROSETTA_POFILENAMES=('pr44.po',), ROSETTA_LANGUAGES=(('xx', 'dummy language'),)
    )
    def test_30_pofile_names(self):
        os.unlink(self.dest_file)
        destfile = os.path.normpath(
            os.path.join(self.curdir, '../locale/xx/LC_MESSAGES/pr44.po')
        )
        shutil.copy(
            os.path.normpath(os.path.join(self.curdir, './pr44.po.template')), destfile
        )

        r = self.client.get(self.third_party_file_list_url)
        self.assertTrue('xx/LC_MESSAGES/pr44.po' in r.content.decode())

        r = self.client.get(self.xx_form_url)
        self.assertTrue('dummy language' in r.content.decode())

        # (Clean up)
        os.unlink(destfile)

    def test_31_pr_102__exclude_paths(self):
        r = self.client.get(self.third_party_file_list_url)
        self.assertContains(r, 'rosetta/locale/xx/LC_MESSAGES/django.po')
        exclude_path = os.path.normpath(os.path.join(self.curdir, '../locale'))
        with self.settings(ROSETTA_EXCLUDED_PATHS=exclude_path):
            r = self.client.get(self.third_party_file_list_url)
            self.assertNotContains(r, 'rosetta/locale/xx/LC_MESSAGES/django.po')

    def test_32_pr_103__language_groups(self):
        from django.contrib.auth.models import User, Group

        # Default behavior: non-admins need to be in a translators group; they
        # see all catalogs
        translators = Group.objects.create(name='translators')
        translators_xx = Group.objects.create(name='translators-xx')

        user4 = User.objects.create_user('test_admin4', 'test@test3.com', 'test_password')
        user4.groups.add(translators)
        user4.is_superuser = False
        user4.is_staff = True
        user4.save()

        with self.settings(ROSETTA_LANGUAGE_GROUPS=False):
            self.client.login(username='test_admin4', password='test_password')
            r = self.client.get(self.third_party_file_list_url)
            self.assertContains(r, 'rosetta/locale/xx/LC_MESSAGES/django.po')

        with self.settings(ROSETTA_LANGUAGE_GROUPS=True):
            r = self.client.get(self.third_party_file_list_url)
            self.assertNotContains(r, 'rosetta/locale/xx/LC_MESSAGES/django.po')
            # Now add them to the custom group
            user4.groups.add(translators_xx)
            r = self.client.get(self.third_party_file_list_url)
            self.assertContains(r, 'rosetta/locale/xx/LC_MESSAGES/django.po')

    @override_settings(
        ROSETTA_ENABLE_REFLANG=True, ROSETTA_LANGUAGES=(('xx', 'dummy language'),)
    )
    def test_33_reflang(self):
        self.copy_po_file_from_template('./django.po.issue60.template')
        r = self.client.get(self.xx_form_url)

        # Verify that there's an option to select a reflang
        self.assertTrue(
            '<option value="?ref_lang=xx">dummy language</option>' in r.content.decode()
        )

        r = self.client.get(self.xx_form_url + '?ref_lang=xx')
        # The translated string in the test PO file ends up in the "Reference" column
        self.assertTrue(
            '<span class="message">translated-string1</span>' in r.content.decode()
        )

    def test_show_occurrences(self):
        r = self.client.get(self.xx_form_url)
        # Verify that occurrences in view
        self.assertTrue('<td class="location">' in r.content.decode())
        with self.settings(ROSETTA_SHOW_OCCURRENCES=False):
            r = self.client.get(self.xx_form_url)
            # Verify that occurrences not in view
            self.assertFalse('<td class="location">' in r.content.decode())

    def test_34_issue_113_app_configs(self):
        r = self.client.get(self.all_file_list_url)
        self.assertTrue('rosetta/files/all/xx/1/">Test_App' in r.content.decode())

    @override_settings(ROSETTA_STORAGE_CLASS='rosetta.storage.CacheRosettaStorage')
    def test_35_issue_135_display_exception_messages(self):
        # Note: the old version of this test looked for a 'Permission denied'
        # message reflected in the response. That behavior has now changed so
        # that changes that can't be persisted through the filesystem .po file
        # are saved to the cached version of the .po file.
        self.copy_po_file_from_template('./django.po.template')

        r = self.client.get(self.xx_form_url + '?msg_filter=untranslated')
        self.assertContains(r, 'm_e48f149a8b2e8baa81b816c0edf93890')

        # make the pofile read-only
        os.chmod(self.dest_file, 292)  # 0444

        # post a translation
        data = {'m_e48f149a8b2e8baa81b816c0edf93890': 'Hello, world'}
        self.client.post(self.xx_form_url, data, follow=True)

        # Confirm that the filesystem file hasn't changed
        tmpl_path = os.path.normpath(os.path.join(self.curdir, 'django.po.template'))
        self.assertTrue(filecmp.cmp(tmpl_path, self.dest_file))

        # Confirm that the cached version has been updated
        cache_key = 'po-file-%s' % self.dest_file
        request = RequestFactory().get(self.xx_form_url)
        request.user = self.user
        request.session = self.client.session
        storage = get_storage(request)

        po_file = storage.get(cache_key)
        entry = po_file.find('String 2')
        self.assertEqual(entry.msgstr, 'Hello, world')

        # cleanup
        os.chmod(self.dest_file, 420)  # 0644

    def test_36_issue_142_complex_locales(self):
        r = self.client.get(self.all_file_list_url)
        self.assertContains(r, 'locale/bs-Cyrl-BA/LC_MESSAGES/django.po')

    @override_settings(ROSETTA_LANGUAGES=(('yy-Anot', u'Yet Another dummy language'),))
    def test_37_issue_133_complex_locales(self):
        r = self.client.get(self.all_file_list_url)
        self.assertContains(r, 'locale/yy-Anot/LC_MESSAGES/django.po')

    def test_38_issue_161_more_weird_locales(self):
        r = self.client.get(self.all_file_list_url)
        self.assertTrue(r, 'locale/zh_Hans/LC_MESSAGES/django.po')

    def test_39_invalid_get_page(self):
        url = self.xx_form_url + '?filter=untranslated'

        r = self.client.get(url)  # Page not specified
        self.assertEqual(r.context['page'], 1)

        r = self.client.get(url + '&page=')  # No number given
        self.assertEqual(r.context['page'], 1)

        r = self.client.get(url + '&page=9999')  # Too-high number given
        self.assertEqual(r.context['page'], 1)

        r = self.client.get(url + '&page=x')  # Non-number given
        self.assertEqual(r.context['page'], 1)

    def test_40_issue_155_auto_compile(self):
        def file_hash(file_string):
            with open(file_string, encoding="latin-1") as file:
                file_content = file.read().encode('utf-8')
            return hashlib.md5(file_content).hexdigest()

        def message_hashes():
            r = self.client.get(self.xx_form_url)
            return {m.msgid: 'm_' + m.md5hash for m in r.context['rosetta_messages']}

        po_file = self.dest_file
        mo_file = self.dest_file[:-3] + '.mo'

        # MO file will be compiled by default.
        # Get PO and MO files into an initial reference state (MO will be
        # created or updated)
        msg_hashes = message_hashes()
        data = {msg_hashes['String 1']: 'Translation 1'}
        self.client.post(self.xx_form_url, data)
        po_file_hash_before, mo_file_hash_before = file_hash(po_file), file_hash(mo_file)

        # Make a change to the translations
        msg_hashes = message_hashes()
        data = {msg_hashes['String 1']: 'Translation 2'}
        self.client.post(self.xx_form_url, data)

        # Get the new hashes of the PO and MO file contents
        po_file_hash_after, mo_file_hash_after = file_hash(po_file), file_hash(mo_file)

        # Both the PO and MO should have changed
        self.assertNotEqual(po_file_hash_before, po_file_hash_after)
        self.assertNotEqual(mo_file_hash_before, mo_file_hash_after)

        # Disable auto-compilation of the MO when the PO is saved
        with self.settings(ROSETTA_AUTO_COMPILE=False):
            # Make a change to the translations
            po_file_hash_before, mo_file_hash_before = (
                po_file_hash_after,
                mo_file_hash_after,
            )
            msg_hashes = message_hashes()
            data = {msg_hashes['String 1']: "Translation 3"}
            self.client.post(self.xx_form_url, data)
            po_file_hash_after, mo_file_hash_after = (
                file_hash(po_file),
                file_hash(mo_file),
            )

            # Only the PO should have changed, the MO should be unchanged
            self.assertNotEqual(po_file_hash_before, po_file_hash_after)
            self.assertEqual(mo_file_hash_before, mo_file_hash_after)

            # Verify that translating another string also leaves the MO unchanged
            po_file_hash_before, mo_file_hash_before = (
                po_file_hash_after,
                mo_file_hash_after,
            )
            msg_hashes = message_hashes()
            data = {msg_hashes['String 2']: "Translation 4"}
            self.client.post(self.xx_form_url, data)
            po_file_hash_after, mo_file_hash_after = (
                file_hash(po_file),
                file_hash(mo_file),
            )

            self.assertNotEqual(po_file_hash_before, po_file_hash_after)
            self.assertEqual(mo_file_hash_before, mo_file_hash_after)

        with self.settings(ROSETTA_AUTO_COMPILE=True):
            po_file_hash_before, mo_file_hash_before = (
                po_file_hash_after,
                mo_file_hash_after,
            )
            msg_hashes = message_hashes()
            data = {msg_hashes['String 2']: "Translation 5"}
            self.client.post(self.xx_form_url, data)
            po_file_hash_after, mo_file_hash_after = (
                file_hash(po_file),
                file_hash(mo_file),
            )

            self.assertNotEqual(po_file_hash_before, po_file_hash_after)
            self.assertNotEqual(mo_file_hash_before, mo_file_hash_after)

    def test_41_pr_176_embed_in_admin(self):
        resp = self.client.get(reverse('admin:index'))
        self.assertContains(resp, 'app-rosetta module')

    def _setup_view(self, view, request, *args, **kwargs):
        """Mimic as_view() returned callable, but returns view instance.

        args and kwargs are the same you would pass to ``reverse()``
        (From http://tech.novapost.fr/django-unit-test-your-views-en.html.)
        """
        view.request = request
        view.args = args
        view.kwargs = kwargs
        return view

    def test_42_view_property_po_file_is_writable(self):
        """Confirm that we're accurately determining the filesystem write-perms
        on our .po file.
        """
        self.copy_po_file_from_template('./django.po.template')

        # By default, we're writable
        request = RequestFactory().get(self.xx_form_url)
        request.user = self.user
        kwargs = {'po_filter': 'third-party', 'lang_id': 'xx', 'idx': 0}
        view = self._setup_view(
            view=views.TranslationFormView(), request=request, **kwargs
        )
        self.assertTrue(view.po_file_is_writable)

        # Now try again with the file not writable. (Regenerate the view, since
        # this po_file_is_writable is cached for the life of the request.)
        # make the pofile read-only
        os.chmod(self.dest_file, 292)  # 0444
        view = self._setup_view(
            view=views.TranslationFormView(), request=request, **kwargs
        )
        self.assertFalse(view.po_file_is_writable)

        # Cleanup
        os.chmod(self.dest_file, 420)  # 0644

    def test_43_view_property_po_file_path(self):
        """Confirm our class-based views properly parse/validate the path of the
        .po file in question derived from the url kwargs.
        """
        self.copy_po_file_from_template('./django.po.template')

        # By default, when all goes well, we get our existing .po file path
        request = RequestFactory().get(self.xx_form_url)
        request.user = self.user
        kwargs = {'po_filter': 'third-party', 'lang_id': 'xx', 'idx': 0}
        view = self._setup_view(
            view=views.TranslationFormView(), request=request, **kwargs
        )
        self.assertEqual(view.po_file_path, self.dest_file)

        # But if the language isn't an option, we get a 404
        with self.settings(
            ROSETTA_LANGUAGES=[lang for lang, __ in settings.LANGUAGES if lang != 'xx']
        ):
            view = self._setup_view(
                view=views.TranslationFormView(), request=request, **kwargs
            )
            with self.assertRaises(Http404):
                view.po_file_path

        # And if the index doesn't correspond with a file, we get a 404
        new_kwargs = {'po_filter': 'third-party', 'lang_id': 'xx', 'idx': 9}
        view = self._setup_view(
            view=views.TranslationFormView(),
            # Recycle request, even though url kwargs conflict with ones below.
            request=request,
            **new_kwargs
        )
        with self.assertRaises(Http404):
            view.po_file_path

    def test_44_message_search_function(self):
        """Confirm that search of the .po file works across the various message
        fields.
        """
        self.copy_po_file_from_template('./django.po.test44.template')
        url = self.xx_form_url + '?query=%s'

        # Here's the message entry we're considering:
        # #. Translators: consectetur adipisicing
        # #: templates/eiusmod/tempor.html:43
        # msgid "Lorem ipsum"
        # msgstr "dolor sit amet"
        # It is buried at the end of the file, so without searching for it, it
        # shouldn't be on the page
        r = self.client.get(url % '')
        self.assertNotContains(r, 'Lorem')

        # Search msgid
        r = self.client.get(url % 'ipsum')
        self.assertContains(r, 'Lorem')

        # Search msgstr
        r = self.client.get(url % 'dolor')
        self.assertContains(r, 'Lorem')

        # Search occurences
        r = self.client.get(url % 'tempor')
        self.assertContains(r, 'Lorem')

        # Search comments
        r = self.client.get(url % 'adipisicing')
        self.assertContains(r, 'Lorem')

        # Search context
        r = self.client.get(url % 'pellentesque')
        self.assertContains(r, 'Lorem')

    def test_45_issue186_plural_msg_search(self):
        """Confirm that search of the .po file works for plurals."""
        self.copy_po_file_from_template('./django.po.issue186.template')
        url = self.xx_form_url + '?query=%s'

        # Here's the message entry we're considering:
        # msgstr "%d Child"
        # msgid_plural "%d Childrenen"
        # msgstr[0] "%d Tchilt"
        # msgstr[1] "%d Tchildren"

        # First, confirm that we don't ALWAYS see this particular message on the
        # page.
        r = self.client.get(url % 'kids')
        self.assertNotContains(r, 'Child')

        # Search msgid_plural
        r = self.client.get(url % 'childrenen')
        self.assertContains(r, 'Child')

        # Search msgstr[0]
        r = self.client.get(url % 'tchilt')
        self.assertContains(r, 'Child')

        # Search msgstr[1]
        r = self.client.get(url % 'tchildren')
        self.assertContains(r, 'Child')

    def test_46_search_string_with_unicode_symbols(self):
        """Confirm that search works with unicode symbols"""
        url = self.xx_form_url + '?' + urlencode({'query': force_bytes(u'Лорем')})

        # It shouldn't raise
        r = self.client.get(url)
        self.assertEqual(r.status_code, 200)

    @vcr.use_cassette(
        'fixtures/vcr_cassettes/test_47_azure_ajax_translation.yaml',
        match_on=['method', 'scheme', 'host', 'port', 'path', 'query', 'raw_body'],
        record_mode='new_episodes',
    )
    @override_settings(DEEPL_AUTH_KEY=None, AZURE_CLIENT_SECRET="FAKE")
    def test_47_azure_ajax_translation(self):
        r = self.client.get(
            reverse('rosetta.translate_text') + '?from=en&to=fr&text=hello%20world'
        )
        self.assertContains(r, '"Salut tout le monde"')

    @override_settings(ROSETTA_REQUIRES_AUTH=True)
    def test_48_requires_auth_not_respected_issue_203(self):
        self.client.logout()
        r = self.client.get(self.all_file_list_url)
        self.assertRedirects(
            r,
            '{}?next=/rosetta/files/all/'.format(settings.LOGIN_URL),
            fetch_redirect_response=False,
        )
        self.assertEqual(302, r.status_code)

    @override_settings(ROSETTA_REQUIRES_AUTH=False)
    def test_49_requires_auth_not_respected_issue_203(self):
        r = self.client.get(self.all_file_list_url)
        self.assertEqual(200, r.status_code)

    @override_settings(ROSETTA_REQUIRES_AUTH=True, ROSETTA_LOGIN_URL='/custom-url/')
    def test_50_custom_login_url(self):
        self.client.logout()
        r = self.client.get(self.all_file_list_url)
        self.assertRedirects(
            r, '/custom-url/?next=/rosetta/files/all/', fetch_redirect_response=False
        )
        self.assertEqual(302, r.status_code)

    def test_51_rosetta_languages(self):
        self.assertTrue('xx' in dict(settings.LANGUAGES))
        self.assertFalse('yy' in dict(settings.LANGUAGES))

        with self.settings(ROSETTA_LANGUAGES=(('xx', 'foo language'),)):
            r = self.client.get(self.project_file_list_url)
            self.assertTrue('foo language' in r.content.decode())
            self.assertFalse('bar language' in r.content.decode())

        with self.settings(
            ROSETTA_LANGUAGES=(('xx', 'foo language'), ('yy', 'bar language'))
        ):
            r = self.client.get(self.project_file_list_url)
            self.assertTrue('foo language' in r.content.decode())
            self.assertTrue('bar language' in r.content.decode())

    def test_52_deepl_languages_handled_correctly(self):
        """
        If DEEPL_LANGUAGES set in settings, we use that one, if not, we use django's language code.
        """
        if settings.DEEPL_AUTH_KEY:
            with self.settings(DEEPL_LANGUAGES={"fr_FR.utf8": "FR"}):
                r = self.client.get(
                    reverse(
                        "rosetta-form",
                        kwargs={
                            "po_filter": "project",
                            "lang_id": "fr_FR.utf8",
                            "idx": "0",
                        },
                    )
                )
                self.assertContains(r, "var destLangRoot = 'FR'")
            with self.settings(DEEPL_LANGUAGES=None):
                r = self.client.get(
                    reverse(
                        "rosetta-form",
                        kwargs={
                            "po_filter": "project",
                            "lang_id": "fr_FR.utf8",
                            "idx": "0",
                        },
                    )
                )
                self.assertContains(r, "var destLangRoot = 'fr-FR.utf8'.substring(0, 2)")

    def test_198_embed_in_admin_access_control(self):
        resp = self.client.get(reverse('admin:index'))
        self.assertContains(resp, 'rosetta-content-main')

        with self.settings(ROSETTA_ACCESS_CONTROL_FUNCTION=lambda user: False):
            resp = self.client.get(reverse('admin:index'))
            self.assertNotContains(resp, 'rosetta-content-main')


# Stubbed access control function
def no_access(user):
    return False
