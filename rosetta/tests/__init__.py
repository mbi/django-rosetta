# -*- coding: utf-8 -*-
from django.conf import settings
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.template.defaultfilters import floatformat
from django.test import TestCase
from django.test.client import Client
from rosetta.conf import settings as rosetta_settings
from rosetta.signals import entry_changed, post_save
import os, shutil, django


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
    
    
    def __init__(self, *args,**kwargs):
        super(RosettaTestCase,self).__init__(*args,**kwargs)
        self.curdir = os.path.dirname(__file__)
        self.dest_file = os.path.normpath(os.path.join(self.curdir, '../locale/xx/LC_MESSAGES/django.po'))
        self.django_version_major, self.django_version_minor = django.VERSION[0],django.VERSION[1]
        

    def setUp(self):
        user    = User.objects.create_user('test_admin', 'test@test.com', 'test_password')
        user2   = User.objects.create_user('test_admin2', 'test@test2.com', 'test_password')
        user3   = User.objects.create_user('test_admin3', 'test@test2.com', 'test_password')
        
        user.is_superuser, user2.is_superuser, user3.is_superuser = True,True, True
        user.is_staff, user2.is_staff, user3.is_staff = True,True, False
        
        user.save()
        user2.save()
        user3.save()
        
        self.client2 = Client()
        
        self.client.login(username='test_admin',password='test_password')
        self.client2.login(username='test_admin2',password='test_password')
        
        settings.LANGUAGES = (('xx','dummy language'),)
        
        

    def test_1_ListLoading(self):
        r = self.client.get(reverse('rosetta-pick-file') +'?filter=third-party')
        r = self.client.get(reverse('rosetta-pick-file'))
        self.assertTrue(os.path.normpath('rosetta/locale/xx/LC_MESSAGES/django.po') in r.content)
        
        
    def test_2_PickFile(self):
        r = self.client.get(reverse('rosetta-pick-file') +'?filter=third-party')
        r = self.client.get(reverse('rosetta-language-selection', args=('xx',0,), kwargs=dict() ) +'?rosetta')
        r = self.client.get(reverse('rosetta-home'))
        
        self.assertTrue('dummy language' in r.content)
        
    def test_3_DownloadZIP(self):
        r = self.client.get(reverse('rosetta-pick-file') +'?filter=third-party')
        
        r = self.client.get(reverse('rosetta-language-selection', args=('xx',0,), kwargs=dict() ) +'?rosetta')
        r = self.client.get(reverse('rosetta-home'))
        r = self.client.get(reverse('rosetta-download-file' ) +'?rosetta')
        self.assertTrue ('content-type' in r._headers.keys() )
        self.assertTrue ('application/x-zip' in r._headers.get('content-type'))
    
    def test_4_DoChanges(self):
        
        # copy the template file
        shutil.copy(self.dest_file, self.dest_file + '.orig')
        shutil.copy(os.path.normpath(os.path.join(self.curdir,'./django.po.template')), self.dest_file)

        # Load the template file
        r = self.client.get(reverse('rosetta-pick-file')  +'?filter=third-party')
        r = self.client.get(reverse('rosetta-language-selection', args=('xx',0,), kwargs=dict() ))
        r = self.client.get(reverse('rosetta-home') + '?filter=untranslated')
        r = self.client.get(reverse('rosetta-home'))
        
        # make sure both strings are untranslated
        self.assertTrue('dummy language' in r.content)
        self.assertTrue('String 1' in r.content)
        self.assertTrue('String 2' in r.content)
        self.assertTrue('m_e48f149a8b2e8baa81b816c0edf93890' in r.content)
        
        # post a translation
        r = self.client.post(reverse('rosetta-home'), dict(m_e48f149a8b2e8baa81b816c0edf93890='Hello, world', _next='_next'))
        
        # reload all untranslated strings
        r = self.client.get(reverse('rosetta-language-selection', args=('xx',0,), kwargs=dict() ) +'?rosetta')
        r = self.client.get(reverse('rosetta-home') + '?filter=untranslated')
        r = self.client.get(reverse('rosetta-home'))
        
        # the translated string no longer is up for translation
        self.assertTrue('String 1'  in r.content)
        self.assertTrue('String 2' not in r.content)
        
        # display only translated strings
        r = self.client.get(reverse('rosetta-home') + '?filter=translated')
        r = self.client.get(reverse('rosetta-home'))
        
        # The tranlsation was persisted
        self.assertTrue('String 1' not  in r.content)
        self.assertTrue('String 2' in r.content)
        self.assertTrue('Hello, world' in r.content)
        
        # reset the original file
        shutil.move(self.dest_file+'.orig', self.dest_file)
        

    def test_5_TestIssue67(self):
        # testcase for issue 67: http://code.google.com/p/django-rosetta/issues/detail?id=67
        # copy the template file
        shutil.copy(self.dest_file, self.dest_file + '.orig')
        shutil.copy(os.path.normpath(os.path.join(self.curdir,'./django.po.issue67.template')), self.dest_file)
        
        # Make sure the plurals string is valid
        f_ = open(self.dest_file,'rb')
        content = f_.read()
        f_.close()
        self.assertTrue(u'Hello, world' not in content)
        self.assertTrue(u'|| n%100>=20) ? 1 : 2)' in content)
        del(content)
        
        # Load the template file
        r = self.client.get(reverse('rosetta-pick-file') +'?filter=third-party')
        
        r = self.client.get(reverse('rosetta-language-selection', args=('xx',0,), kwargs=dict() ) +'?rosetta')
        r = self.client.get(reverse('rosetta-home') + '?filter=untranslated')
        r = self.client.get(reverse('rosetta-home'))
        
        # make sure all strings are untranslated
        self.assertTrue('dummy language' in r.content)
        self.assertTrue('String 1' in r.content)
        self.assertTrue('String 2' in r.content)
        self.assertTrue('m_e48f149a8b2e8baa81b816c0edf93890' in r.content)
        
        # post a translation
        r = self.client.post(reverse('rosetta-home'), dict(m_e48f149a8b2e8baa81b816c0edf93890='Hello, world', _next='_next'))
        
        # Make sure the plurals string is still valid
        f_ = open(self.dest_file,'rb')
        content = f_.read()
        f_.close()
        self.assertTrue(u'Hello, world' in content)
        self.assertTrue(u'|| n%100>=20) ? 1 : 2)' in content)
        self.assertTrue(u'or n%100>=20) ? 1 : 2)' not in content)
        del(content)

        shutil.move(self.dest_file + '.orig', self.dest_file)
        

    def test_6_ExcludedApps(self):
        
        rosetta_settings.EXCLUDED_APPLICATIONS = ('rosetta',)
        
        r = self.client.get(reverse('rosetta-pick-file') +'?filter=third-party')
        r = self.client.get(reverse('rosetta-pick-file'))
        self.assertTrue('rosetta/locale/xx/LC_MESSAGES/django.po' not in r.content)
        
        rosetta_settings.EXCLUDED_APPLICATIONS = ()
        
        r = self.client.get(reverse('rosetta-pick-file') +'?rosetta')
        self.assertTrue('rosetta/locale/xx/LC_MESSAGES/django.po' in r.content)
        
    def test_7_selfInApplist(self):    
        self.client.get(reverse('rosetta-pick-file') +'?filter=third-party')
        r = self.client.get(reverse('rosetta-pick-file'))
        self.assertTrue('rosetta/locale/xx/LC_MESSAGES/django.po' in r.content)

        self.client.get(reverse('rosetta-pick-file') + '?filter=project')
        r = self.client.get(reverse('rosetta-pick-file'))
        self.assertTrue('rosetta/locale/xx/LC_MESSAGES/django.po' not in r.content)


    def test_8_hideObsoletes(self):
        r = self.client.get(reverse('rosetta-pick-file') +'?filter=third-party')
        r = self.client.get(reverse('rosetta-pick-file'))
        r = self.client.get(reverse('rosetta-language-selection', args=('xx',0,), kwargs=dict() ))
        
        # not in listing
        for p in range(1,5):
            r = self.client.get(reverse('rosetta-home') + '?page=%d'%p)
            self.assertTrue('dummy language' in r.content)
            self.assertTrue('Les deux' not in r.content)
        
        r = self.client.get(reverse('rosetta-home') + '?query=Les%20Deux')
        self.assertTrue('dummy language' in r.content)
        self.assertTrue('Les deux' not in r.content)


    def test_9_concurrency(self):
        shutil.copy(self.dest_file, self.dest_file + '.orig')
        shutil.copy(os.path.normpath(os.path.join(self.curdir,'./django.po.template')), self.dest_file)
        
        r = self.client.get(reverse('rosetta-pick-file') +'?filter=third-party')
        r = self.client2.get(reverse('rosetta-pick-file') +'?filter=third-party')
        
        self.client.get(reverse('rosetta-language-selection', args=('xx',0,), kwargs=dict() ) )
        self.client2.get(reverse('rosetta-language-selection', args=('xx',0,), kwargs=dict() ))

        # Load the template file
        r   = self.client.get(reverse('rosetta-home') + '?filter=untranslated')
        r   = self.client.get(reverse('rosetta-home'))
        r2  = self.client2.get(reverse('rosetta-home') + '?filter=untranslated')
        r2  = self.client2.get(reverse('rosetta-home'))
        
        self.assertTrue('String 1' in r.content)
        self.assertTrue('String 1' in r2.content)
        self.assertTrue('m_08e4e11e2243d764fc45a5a4fba5d0f2' in r.content)
        
        
        r = self.client.post(reverse('rosetta-home'), dict(m_08e4e11e2243d764fc45a5a4fba5d0f2='Hello, world', _next='_next'))
        r2  = self.client2.get(reverse('rosetta-home'))
        
        # Client 2 reloads the home, forces a reload of the catalog, 
        # the untranslated string1 is now translated
        self.assertTrue('String 1' not in r2.content)
        self.assertTrue('String 2' in r2.content)


        r   = self.client.get(reverse('rosetta-home') + '?filter=untranslated')
        r   = self.client.get(reverse('rosetta-home'))
        r2  = self.client2.get(reverse('rosetta-home') + '?filter=untranslated')
        r2  = self.client2.get(reverse('rosetta-home'))


        self.assertTrue('String 2' in r2.content and 'm_e48f149a8b2e8baa81b816c0edf93890' in r2.content)
        self.assertTrue('String 2' in r.content and 'm_e48f149a8b2e8baa81b816c0edf93890' in r.content)
        
        # client 2 posts!
        r2 = self.client2.post(reverse('rosetta-home'), dict(m_e48f149a8b2e8baa81b816c0edf93890='Hello, world, from client two!', _next='_next'))
        self.assertTrue('save-conflict' not in r2.content)
        
        
        # uh-oh here comes client 1
        r = self.client.post(reverse('rosetta-home'), dict(m_e48f149a8b2e8baa81b816c0edf93890='Hello, world, from client one!', _next='_next'))
        # An error message is displayed
        self.assertTrue('save-conflict' in r.content)
        
        # Both clients show all strings, error messages are gone
        r  = self.client.get(reverse('rosetta-home') +'?filter=translated')
        self.assertTrue('save-conflict' not in r.content)
        r2  = self.client2.get(reverse('rosetta-home') +'?filter=translated')
        self.assertTrue('save-conflict' not in r2.content)
        r  = self.client.get(reverse('rosetta-home'))
        self.assertTrue('save-conflict' not in r.content)
        r2  = self.client2.get(reverse('rosetta-home'))
        self.assertTrue('save-conflict' not in r2.content)
        
        # Both have client's two version
        self.assertTrue('Hello, world, from client two!' in r.content)
        self.assertTrue('Hello, world, from client two!' in r2.content)
        self.assertTrue('save-conflict' not in r2.content)
        self.assertTrue('save-conflict' not in r.content)
        
        
        
        # reset the original file
        shutil.move(self.dest_file+'.orig', self.dest_file)

        
    def test_10_issue_79_num_entries(self):
        shutil.copy(self.dest_file, self.dest_file + '.orig')
        shutil.copy(os.path.normpath(os.path.join(self.curdir,'./django.po.issue79.template')), self.dest_file)
        
        self.client.get(reverse('rosetta-pick-file') +'?filter=third-party')
        r = self.client.get(reverse('rosetta-pick-file'))
        
        self.assertTrue('<td class="ch-messages r">1</td>' in r.content)
        self.assertTrue('<td class="ch-progress r">%s%%</td>' % str(floatformat(0.0, 2)) in r.content)
        self.assertTrue('<td class="ch-obsolete r">1</td>' in r.content)
        
        # reset the original file
        shutil.move(self.dest_file+'.orig', self.dest_file)
    
    def test_11_issue_80_tab_indexes(self):
        self.client.get(reverse('rosetta-pick-file')+'?filter=third-party')
        r = self.client.get(reverse('rosetta-language-selection', args=('xx',0,), kwargs=dict() ))
        r = self.client.get(reverse('rosetta-home'))
        self.assertTrue('tabindex="3"' in r.content)


    def test_12_issue_82_staff_user(self):
        settings.ROSETTA_REQUIRES_AUTH = True

        self.client3 = Client()
        self.client3.login(username='test_admin3',password='test_password')

        self.client3.get(reverse('rosetta-pick-file')+'?filter=third-party')
        r = self.client3.get(reverse('rosetta-language-selection', args=('xx',0,), kwargs=dict() ))
        r = self.client3.get(reverse('rosetta-home'))
        self.assertTrue(not r.content)

        settings.ROSETTA_REQUIRES_AUTH = False

        self.client3.get(reverse('rosetta-pick-file')+'?filter=third-party')
        r = self.client3.get(reverse('rosetta-language-selection', args=('xx',0,), kwargs=dict() ))
        r = self.client3.get(reverse('rosetta-home'))
        self.assertFalse(not r.content)

    
    def test_13_catalog_filters(self):
        settings.LANGUAGES = (('fr','French'),('xx','Dummy Language'),)
        
        
        
        self.client.get(reverse('rosetta-pick-file')+'?filter=third-party')
        r = self.client.get(reverse('rosetta-pick-file'))
        self.assertTrue(os.path.normpath('rosetta/locale/xx/LC_MESSAGES/django.po') in r.content)
        self.assertTrue(('contrib') not in r.content)
        
        self.client.get(reverse('rosetta-pick-file')+'?filter=django')
        r = self.client.get(reverse('rosetta-pick-file'))
        self.assertTrue(os.path.normpath('rosetta/locale/xx/LC_MESSAGES/django.po') not in r.content)
        
        if self.django_version_major >=1 and self.django_version_minor >=3:
            self.assertTrue(('contrib') in r.content)
        
        self.client.get(reverse('rosetta-pick-file')+'?filter=all')
        r = self.client.get(reverse('rosetta-pick-file'))
        self.assertTrue(os.path.normpath('rosetta/locale/xx/LC_MESSAGES/django.po') in r.content)
        
        if self.django_version_major >=1 and self.django_version_minor >=3:
            self.assertTrue(('contrib') in r.content)
        
        self.client.get(reverse('rosetta-pick-file')+'?filter=project')
        r = self.client.get(reverse('rosetta-pick-file'))
        self.assertTrue(os.path.normpath('rosetta/locale/xx/LC_MESSAGES/django.po') not in r.content)
        
        if self.django_version_major >=1 and self.django_version_minor >=3:
            self.assertTrue(('contrib') not in r.content)


    def test_14_issue_99_context_and_comments(self):
        self.client.get(reverse('rosetta-pick-file')+'?filter=third-party')
        r = self.client.get(reverse('rosetta-language-selection', args=('xx',0,), kwargs=dict() ))
        r = self.client.get(reverse('rosetta-home'))
        self.assertTrue('This is a text of the base template' in r.content)
        self.assertTrue('Context hint' in r.content)


    def test_14_issue_87_entry_changed_signal(self):
        # copy the template file
        shutil.copy(self.dest_file, self.dest_file + '.orig')
        shutil.copy(os.path.normpath(os.path.join(self.curdir,'./django.po.template')), self.dest_file)
        
        
        self.client.get(reverse('rosetta-pick-file')+'?filter=third-party')
        r = self.client.get(reverse('rosetta-language-selection', args=('xx',0,), kwargs=dict() ))
        r = self.client.get(reverse('rosetta-home'))
        
        @receiver(entry_changed)
        def test_receiver(sender, **kwargs):
            self.test_old_msgstr = kwargs.get('old_msgstr')
            self.test_new_msgstr = sender.msgstr
            self.test_msg_id = sender.msgid
    
        
        self.assertTrue('m_e48f149a8b2e8baa81b816c0edf93890' in r.content)

        # post a translation
        r = self.client.post(reverse('rosetta-home'), dict(m_e48f149a8b2e8baa81b816c0edf93890='Hello, world', _next='_next'))
        
        self.assertTrue(self.test_old_msgstr == '')
        self.assertTrue(self.test_new_msgstr == 'Hello, world')
        self.assertTrue(self.test_msg_id == 'String 2')
        
        del(self.test_old_msgstr, self.test_new_msgstr, self.test_msg_id)
        
        # reset the original file
        shutil.move(self.dest_file+'.orig', self.dest_file)

    def test_15_issue_101_post_save_signal(self):
        # copy the template file
        shutil.copy(self.dest_file, self.dest_file + '.orig')
        shutil.copy(os.path.normpath(os.path.join(self.curdir,'./django.po.template')), self.dest_file)
        
        
        self.client.get(reverse('rosetta-pick-file')+'?filter=third-party')
        r = self.client.get(reverse('rosetta-language-selection', args=('xx',0,), kwargs=dict() ))
        r = self.client.get(reverse('rosetta-home'))
        
        @receiver(post_save)
        def test_receiver(sender, **kwargs):
            self.test_sig_lang = kwargs.get('language_code')
    
        self.assertTrue('m_e48f149a8b2e8baa81b816c0edf93890' in r.content)

        # post a translation
        r = self.client.post(reverse('rosetta-home'), dict(m_e48f149a8b2e8baa81b816c0edf93890='Hello, world', _next='_next'))
        
        self.assertTrue(self.test_sig_lang == 'xx')
        del(self.test_sig_lang)
        # reset the original file
        shutil.move(self.dest_file+'.orig', self.dest_file)
        

    def test_16_issue_103_post_save_signal_has_request(self):
        # copy the template file
        shutil.copy(self.dest_file, self.dest_file + '.orig')
        shutil.copy(os.path.normpath(os.path.join(self.curdir,'./django.po.template')), self.dest_file)


        self.client.get(reverse('rosetta-pick-file')+'?filter=third-party')
        r = self.client.get(reverse('rosetta-language-selection', args=('xx',0,), kwargs=dict() ))
        r = self.client.get(reverse('rosetta-home'))

        @receiver(post_save)
        def test_receiver(sender, **kwargs):
            self.test_16_has_request = 'request' in kwargs

        self.assertTrue('m_e48f149a8b2e8baa81b816c0edf93890' in r.content)

        # post a translation
        r = self.client.post(reverse('rosetta-home'), dict(m_e48f149a8b2e8baa81b816c0edf93890='Hello, world', _next='_next'))

        self.assertTrue(self.test_16_has_request)
        del(self.test_16_has_request)
        # reset the original file
        shutil.move(self.dest_file + '.orig', self.dest_file)

    def test_17_Test_Issue_gh24(self):
        shutil.copy(self.dest_file, self.dest_file + '.orig')
        shutil.copy(os.path.normpath(os.path.join(self.curdir, './django.po.issue24gh.template')), self.dest_file)

        self.client.get(reverse('rosetta-pick-file') + '?filter=third-party')
        r = self.client.get(reverse('rosetta-language-selection', args=('xx', 0, ), kwargs=dict()))
        r = self.client.get(reverse('rosetta-home'))

        self.assertTrue('m_bb9d8fe6159187b9ea494c1b313d23d4' in r.content)

        # post a translation, it should have properly wrapped lines
        r = self.client.post(reverse('rosetta-home'), dict(m_bb9d8fe6159187b9ea494c1b313d23d4='Lorem ipsum dolor sit amet, consectetuer adipiscing elit. Aenean commodo ligula eget dolor. Aenean massa. Cum sociis natoque penatibus et magnis dis parturient montes, nascetur ridiculus mus. Donec quam felis, ultricies nec, pellentesque eu, pretium quis, sem. Nulla consequat massa quis enim. Donec pede justo, fringilla vel, aliquet nec, vulputate eget, arcu. In enim justo, rhoncus ut, imperdiet a, venenatis vitae, justo. Nullam dictum felis eu pede mollis pretium.', _next='_next'))
        pofile_content = open(self.dest_file, 'r').read()
        self.assertTrue('"pede mollis pretium."' in pofile_content)

        # Again, with unwrapped lines
        shutil.copy(os.path.normpath(os.path.join(self.curdir, './django.po.issue24gh.template')), self.dest_file)
        self.client.get(reverse('rosetta-pick-file') + '?filter=third-party')
        r = self.client.get(reverse('rosetta-language-selection', args=('xx', 0, ), kwargs=dict()))
        r = self.client.get(reverse('rosetta-home'))
        self.assertTrue('m_bb9d8fe6159187b9ea494c1b313d23d4' in r.content)
        rosetta_settings.POFILE_WRAP_WIDTH = 0
        r = self.client.post(reverse('rosetta-home'), dict(m_bb9d8fe6159187b9ea494c1b313d23d4='Lorem ipsum dolor sit amet, consectetuer adipiscing elit. Aenean commodo ligula eget dolor. Aenean massa. Cum sociis natoque penatibus et magnis dis parturient montes, nascetur ridiculus mus. Donec quam felis, ultricies nec, pellentesque eu, pretium quis, sem. Nulla consequat massa quis enim. Donec pede justo, fringilla vel, aliquet nec, vulputate eget, arcu. In enim justo, rhoncus ut, imperdiet a, venenatis vitae, justo. Nullam dictum felis eu pede mollis pretium.', _next='_next'))
        pofile_content = open(self.dest_file, 'r').read()
        self.assertTrue('felis eu pede mollis pretium."' in pofile_content)

        shutil.move(self.dest_file + '.orig', self.dest_file)
