import hashlib
import json
import os
import os.path
import re
import unicodedata
import uuid
import zipfile

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import user_passes_test
from django.core.paginator import Paginator
from django.http import (
    Http404,
    HttpResponse,
    HttpResponseRedirect,
    JsonResponse
)
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.utils.encoding import force_bytes
from django.utils.functional import Promise, cached_property
from django.utils.translation import ugettext_lazy as _
from django.views.decorators.cache import never_cache
from django.views.generic import TemplateView, View

import requests
import six
from polib import pofile

from . import get_version as get_rosetta_version
from .access import can_translate, can_translate_language
from .conf import settings as rosetta_settings
from .poutil import find_pos, pagination_range, timestamp_with_timezone
from .signals import entry_changed, post_save
from .storage import get_storage


try:
    # Python 3
    from urllib.parse import urlencode
except ImportError:
    # Python 2
    from urllib import urlencode


def get_app_name(path):
    return path.split('/locale')[0].split('/')[-1]


class LoginURL(Promise):
    """
    Tests friendly login URL, url is resolved at runtime.
    """
    def __str__(self):
        return rosetta_settings.LOGIN_URL


@method_decorator(never_cache, 'dispatch')
@method_decorator(user_passes_test(lambda user: can_translate(user), LoginURL()), 'dispatch')
class RosettaBaseMixin(object):
    """A mixin class for Rosetta's class-based views. It provides:
    * security (see class decorators)
    * a property for the 'po_filter' url argument
    """

    def dispatch(self, *args, **kwargs):
        return super(RosettaBaseMixin, self).dispatch(*args, **kwargs)

    @cached_property
    def po_filter(self):
        """Return the filter applied to all of the .po files under consideration
        to determine which file is currently being translated. Options are:
        'all', 'django', 'third-party', 'project'.

        If the filter isn't in this list, throw a 404.
        """
        po_filter = self.kwargs.get('po_filter')
        if po_filter not in {'all', 'django', 'third-party', 'project'}:
            raise Http404
        return po_filter


class RosettaFileLevelMixin(RosettaBaseMixin):
    """Mixin for dealing with views that work specifically with a single
    .po file. In addition to what the super class brings, it adds the following
    properties:
    * language_id (e.g. 'fr'); derived from url, and validated
    * po_file_path (filesystem path to catalog)
    * po_file (pofile object)
    * po_file_is_writable (bool: do we have filesystem write perms to file)
    """
    def _request_request(self, key, default=None):
        if key in self.request.GET:
            return self.request.GET.get(key)
        elif key in self.request.POST:
            return self.request.POST.get(key)
        return default

    @cached_property
    def language_id(self):
        """Determine/return the language id from the url kwargs, after
        validating that:
        1. the language is in rosetta_settings.ROSETTA_LANGUAGES, and
        2. the current user is permitted to translate that language

        (If either of the above fail, throw a 404.)
        """
        # (Formerly known as "rosetta_i18n_lang_code")
        lang_id = self.kwargs['lang_id']
        if lang_id not in {l[0] for l in rosetta_settings.ROSETTA_LANGUAGES}:
            raise Http404
        if not can_translate_language(self.request.user, lang_id):
            raise Http404
        return lang_id

    @cached_property
    def po_file_path(self):
        """Based on the url kwargs, infer and return the path to the .po file to
        be shown/updated.

        Throw a 404 if a file isn't found.
        """
        # This was formerly referred to as 'rosetta_i18n_fn'
        idx = self.kwargs['idx']
        idx = int(idx)  # idx matched url re expression; calling int() is safe

        third_party_apps = self.po_filter in ('all', 'third-party')
        django_apps = self.po_filter in ('all', 'django')
        project_apps = self.po_filter in ('all', 'project')

        po_paths = find_pos(self.language_id,
                            project_apps=project_apps,
                            django_apps=django_apps,
                            third_party_apps=third_party_apps,
                            )
        po_paths.sort(key=get_app_name)

        try:
            path = po_paths[idx]
        except IndexError:
            raise Http404
        return path

    @cached_property
    def po_file(self):
        """Return the parsed .po file that is currently being translated/viewed.

        (Note that this parsing also involves marking up each entry with a hash
        of its contents.)
        """
        if self.po_file_is_writable:
            # If we can write changes to file, then we pull it up fresh with
            # each request.
            # XXX: brittle; what if this path doesn't exist? Isn't a .po file?
            po_file = pofile(self.po_file_path,
                             wrapwidth=rosetta_settings.POFILE_WRAP_WIDTH)
            for entry in po_file:
                # Entry is an object representing a single entry in the catalog.
                # We interate through the *entire catalog*, pasting a hashed
                # value of the meat of each entry on its side in an attribute
                # called "md5hash".
                str_to_hash = (
                    six.text_type(entry.msgid) +
                    six.text_type(entry.msgstr) +
                    six.text_type(entry.msgctxt or '')
                ).encode('utf8')
                entry.md5hash = hashlib.md5(str_to_hash).hexdigest()
        else:
            storage = get_storage(self.request)
            po_file = storage.get(self.po_file_cache_key, None)
            if not po_file:
                po_file = pofile(self.po_file_path)
                for entry in po_file:
                    # Entry is an object representing a single entry in the
                    # catalog. We interate through the entire catalog, pasting
                    # a hashed value of the meat of each entry on its side in
                    # an attribute called "md5hash".
                    str_to_hash = (
                        six.text_type(entry.msgid) +
                        six.text_type(entry.msgstr) +
                        six.text_type(entry.msgctxt or '')
                    ).encode('utf8')
                    entry.md5hash = hashlib.new('md5', str_to_hash).hexdigest()
                storage.set(self.po_file_cache_key, po_file)
        return po_file

    @cached_property
    def po_file_cache_key(self):
        """Return the cache key used to save/access the .po file (when actually
        persisted in cache).
        """
        return 'po-file-%s' % self.po_file_path

    @cached_property
    def po_file_is_writable(self):
        """Return True if we're able (in terms of file system permissions) to
        write out changes to the .po file we're translating.
        """
        # (This was formerly called 'rosetta_i18n_write'.)
        return os.access(self.po_file_path, os.W_OK)


class TranslationFileListView(RosettaBaseMixin, TemplateView):
    """Lists the languages, the gettext catalog files that can be translated,
    and their translation progress for a filtered list of apps/projects.
    """
    http_method_names = ['get']
    template_name = 'rosetta/file-list.html'

    def get_context_data(self, **kwargs):
        context = super(TranslationFileListView, self).get_context_data(**kwargs)

        third_party_apps = self.po_filter in ('all', 'third-party')
        django_apps = self.po_filter in ('all', 'django')
        project_apps = self.po_filter in ('all', 'project')

        languages = []
        has_pos = False
        for language in rosetta_settings.ROSETTA_LANGUAGES:
            if not can_translate_language(self.request.user, language[0]):
                continue

            po_paths = find_pos(language[0],
                                project_apps=project_apps,
                                django_apps=django_apps,
                                third_party_apps=third_party_apps,
                                )
            po_files = [(get_app_name(l), os.path.realpath(l), pofile(l)) for l in po_paths]
            po_files.sort(key=lambda app: app[0])
            languages.append((language[0], _(language[1]), po_files))
            has_pos = has_pos or bool(po_paths)

        context['version'] = get_rosetta_version()
        context['languages'] = languages
        context['has_pos'] = has_pos
        context['po_filter'] = self.po_filter
        return context


class TranslationFormView(RosettaFileLevelMixin, TemplateView):
    """Show a form with a page's worth of messages to be translated; handle its
    submission by updating cached pofile and, if possible, writing out changes
    to existing .po file.

    Query strings that affect what's shown:
    * msg_filter: filters which messages are displayed. One of 'all', 'fuzzy',
      'translated', and 'untranslated'
    * ref_lang: specifies which language should be shown as the source. Only
      applicable when REF_LANG setting is set to True
    * page: which page (number) should be shown of the paginated results (with
      msg_filter or query applied)
    * query: a search string, where only matches are shown. Fields that are
      searched include: source, translated text, "occurence" file path, or
      context hints.
    """
    # Note: due to the unorthodox nature of the form itself, we're not using
    # Django's generic FormView as our base class.
    http_method_names = ['get', 'post']
    template_name = 'rosetta/form.html'

    def fix_nls(self, in_, out_):
        """Fixes submitted translations by filtering carriage returns and pairing
        newlines at the begging and end of the translated string with the original
        """
        if 0 == len(in_) or 0 == len(out_):
            return out_

        if "\r" in out_ and "\r" not in in_:
            out_ = out_.replace("\r", '')

        if "\n" == in_[0] and "\n" != out_[0]:
            out_ = "\n" + out_
        elif "\n" != in_[0] and "\n" == out_[0]:
            out_ = out_.lstrip()
        if 0 == len(out_):
            pass
        elif "\n" == in_[-1] and "\n" != out_[-1]:
            out_ = out_ + "\n"
        elif "\n" != in_[-1] and "\n" == out_[-1]:
            out_ = out_.rstrip()
        return out_

    def post(self, request, *args, **kwargs):
        """The only circumstances when we POST is to submit the main form, both
        updating translations (if any changed) and advancing to the next page of
        messages.

        There is no notion of validation of this content; as implemented, unknown
        fields are ignored and a generic failure message is shown.

        Submitted changes are saved out to the specified .po file on the
        filesystem if that file is writable, otherwise the cached version of the
        file is updated (so it can be downloaded). Then the user is redirected
        to the next page of messages (if there is one; otherwise they're
        redirected back to the current page).
        """
        # The message text inputs are captured as hashes of their initial
        # contents, preceded by "m_". Messages with plurals end with their
        # variation number.
        single_text_input_regex = re.compile(r'^m_([0-9a-f]+)$')
        plural_text_input_regex = re.compile(r'^m_([0-9a-f]+)_([0-9]+)$')
        file_change = False
        for field_name, new_msgstr in request.POST.items():
            md5hash = None

            if plural_text_input_regex.match(field_name):
                md5hash, plural_id = plural_text_input_regex.match(field_name).groups()
                md5hash = str(md5hash)
                # polib parses .po files into unicode strings, but
                # doesn't bother to convert plural indexes to int,
                # so we need unicode here.
                plural_id = six.text_type(plural_id)

                # Above no longer true as of Polib 1.0.4
                if plural_id and plural_id.isdigit():
                    plural_id = int(plural_id)

            elif single_text_input_regex.match(field_name):
                md5hash = str(single_text_input_regex.match(field_name).groups()[0])
                plural_id = None

            if md5hash is not None:  # Empty string should be processed!
                entry = self.po_file.find(md5hash, 'md5hash')
                # If someone did a makemessage, some entries might
                # have been removed, so we need to check.
                if entry:
                    old_msgstr = entry.msgstr
                    if plural_id is not None:  # 0 is ok!
                        entry.msgstr_plural[plural_id] = self.fix_nls(
                            entry.msgid_plural, new_msgstr
                        )
                    else:
                        entry.msgstr = self.fix_nls(entry.msgid, new_msgstr)

                    is_fuzzy = bool(self.request.POST.get('f_%s' % md5hash, False))
                    old_fuzzy = 'fuzzy' in entry.flags

                    if old_fuzzy and not is_fuzzy:
                        entry.flags.remove('fuzzy')
                    elif not old_fuzzy and is_fuzzy:
                        entry.flags.append('fuzzy')

                    file_change = True

                    if old_msgstr != new_msgstr or old_fuzzy != is_fuzzy:
                        entry_changed.send(sender=entry,
                                           user=request.user,
                                           old_msgstr=old_msgstr,
                                           old_fuzzy=old_fuzzy,
                                           pofile=self.po_file_path,
                                           language_code=self.language_id,
                                           )
                else:
                    messages.error(
                        self.request,
                        _("Some items in your last translation block couldn't "
                          "be saved: this usually happens when the catalog file "
                          "changes on disk after you last loaded it."),
                    )

        if file_change and self.po_file_is_writable:
            try:
                self.po_file.metadata['Last-Translator'] = unicodedata.normalize(
                    'NFKD', u"%s %s <%s>" % (
                        getattr(self.request.user, 'first_name', 'Anonymous'),
                        getattr(self.request.user, 'last_name', 'User'),
                        getattr(self.request.user, 'email', 'anonymous@user.tld')
                    )
                ).encode('ascii', 'ignore')
                self.po_file.metadata['X-Translated-Using'] = u"django-rosetta %s" % (
                    get_rosetta_version())
                self.po_file.metadata['PO-Revision-Date'] = timestamp_with_timezone()
            except UnicodeDecodeError:
                pass

            try:
                self.po_file.save()
                po_filepath, ext = os.path.splitext(self.po_file_path)

                if rosetta_settings.AUTO_COMPILE:
                    self.po_file.save_as_mofile(po_filepath + '.mo')

                post_save.send(sender=None, language_code=self.language_id,
                               request=self.request
                               )
                # Try auto-reloading via the WSGI daemon mode reload mechanism
                should_try_wsgi_reload = (
                    rosetta_settings.WSGI_AUTO_RELOAD and
                    'mod_wsgi.process_group' in self.request.environ and
                    self.request.environ.get('mod_wsgi.process_group', None) and
                    'SCRIPT_FILENAME' in self.request.environ and
                    int(self.request.environ.get('mod_wsgi.script_reloading', 0))
                )
                if should_try_wsgi_reload:
                    try:
                        os.utime(self.request.environ.get('SCRIPT_FILENAME'), None)
                    except OSError:
                        pass
                # Try auto-reloading via uwsgi daemon reload mechanism
                if rosetta_settings.UWSGI_AUTO_RELOAD:
                    try:
                        import uwsgi
                        uwsgi.reload()  # pretty easy right?
                    except:
                        pass  # we may not be running under uwsgi :P
                # XXX: It would be nice to add a success message here!
            except Exception as e:
                messages.error(self.request, e)

        if file_change and not self.po_file_is_writable:
            storage = get_storage(self.request)
            storage.set(self.po_file_cache_key, self.po_file)

        # Reconstitute url to redirect to. Start with determining whether the
        # page number can be incremented.
        paginator = Paginator(self.get_entries(), rosetta_settings.MESSAGES_PER_PAGE)
        try:
            page = int(self._request_request('page', 1))
        except ValueError:
            page = 1  # fall back to page 1
        else:
            if not (0 < page <= paginator.num_pages):
                page = 1
        if page < paginator.num_pages:
            page += 1
        query_string_args = {
            'msg_filter': self.msg_filter,
            'query': self.query,
            'ref_lang': self.ref_lang,
            'page': page,
        }
        # Winnow down the query string args to non-blank ones
        query_string_args = {k: v for k, v in query_string_args.items() if v}
        return HttpResponseRedirect("{url}?{qs}".format(
            url=reverse('rosetta-form', kwargs=self.kwargs),
            qs=urlencode_safe(query_string_args)
        ))

    def get_context_data(self, **kwargs):
        context = super(TranslationFormView, self).get_context_data(**kwargs)
        entries = self.get_entries()
        paginator = Paginator(entries, rosetta_settings.MESSAGES_PER_PAGE)

        # Handle REF_LANG setting; mark up our entries with the reg lang's
        # corresponding translations
        LANGUAGES = list(rosetta_settings.ROSETTA_LANGUAGES)
        if rosetta_settings.ENABLE_REFLANG:
            if self.ref_lang_po_file:
                for o in paginator.object_list:
                    ref_entry = self.ref_lang_po_file.find(o.msgid)
                    if ref_entry and ref_entry.msgstr:
                        o.ref_txt = ref_entry.msgstr
                    else:
                        o.ref_txt = o.msgid
            else:
                for o in paginator.object_list:
                    o.ref_txt = o.msgid
            # XXX: having "MSGID" at the end of the dropdown is really odd, no?
            # Why not instead do this?
            # LANGUAGES = [('', '----')] + list(settings.LANGUAGES)
            LANGUAGES.append(('msgid', 'MSGID'))

        # Determine page number & how pagination links should be displayed
        try:
            page = int(self._request_request('page', 1))
        except ValueError:
            page = 1  # fall back to page 1
        else:
            if not (0 < page <= paginator.num_pages):
                page = 1
        needs_pagination = paginator.num_pages > 1
        if needs_pagination:
            if paginator.num_pages >= 10:
                page_range = pagination_range(1, paginator.num_pages, page)
            else:
                page_range = range(1, 1 + paginator.num_pages)

        rosetta_messages = paginator.page(page).object_list

        # Handle MAIN_LANGUAGE setting, if applicable; mark up each entry
        # in the pagination window with the "main language"'s string.
        main_language_id = rosetta_settings.MAIN_LANGUAGE
        main_language = None
        if main_language_id and main_language_id != self.language_id:
            # Translate from id to language name
            for language in rosetta_settings.ROSETTA_LANGUAGES:
                if language[0] == main_language_id:
                    main_language = _(language[1])
                    break
        if main_language:
            main_lang_po_path = self.po_file_path.replace(
                '/%s/' % self.language_id,
                '/%s/' % main_language_id,
            )
            # XXX: brittle; what if this path doesn't exist? Isn't a .po file?
            main_lang_po = pofile(main_lang_po_path)

            for message in rosetta_messages:
                message.main_lang = main_lang_po.find(message.msgid).msgstr

        # Collect some constants for the template
        rosetta_i18n_lang_name = six.text_type(
            dict(rosetta_settings.ROSETTA_LANGUAGES).get(self.language_id)
        )
        # "bidi" as in "bi-directional"
        rosetta_i18n_lang_bidi = self.language_id.split('-')[0] in settings.LANGUAGES_BIDI
        query_string_args = {}
        if self.msg_filter:
            query_string_args['msg_filter'] = self.msg_filter
        if self.query:
            query_string_args['query'] = self.query
        if self.ref_lang:
            query_string_args['ref_lang'] = self.ref_lang
        # Base for pagination links; the page num itself is added in template
        pagination_query_string_base = urlencode_safe(query_string_args)
        # Base for msg filter links; it doesn't make sense to persist page
        # numbers in these links. We just pass in ref_lang, if it's set.
        filter_query_string_base = urlencode_safe(
            {k: v for k, v in query_string_args.items() if k == 'ref_lang'}
        )

        context.update({
            'version': get_rosetta_version(),
            'LANGUAGES': LANGUAGES,
            'rosetta_settings': rosetta_settings,
            'rosetta_i18n_lang_name': rosetta_i18n_lang_name,
            'rosetta_i18n_lang_code': self.language_id,
            'rosetta_i18n_lang_code_normalized': self.language_id.replace('_', '-'),
            'rosetta_i18n_lang_bidi': rosetta_i18n_lang_bidi,
            'rosetta_i18n_filter': self.msg_filter,
            'rosetta_i18n_write': self.po_file_is_writable,
            'rosetta_messages': rosetta_messages,
            'page_range': needs_pagination and page_range,
            'needs_pagination': needs_pagination,
            'main_language': main_language,
            'rosetta_i18n_app': get_app_name(self.po_file_path),
            'page': page,
            'query': self.query,
            'pagination_query_string_base': pagination_query_string_base,
            'filter_query_string_base': filter_query_string_base,
            'paginator': paginator,
            'rosetta_i18n_pofile': self.po_file,
            'ref_lang': self.ref_lang,
        })

        return context

    @cached_property
    def ref_lang(self):
        """Return the language id for the "reference language" (the language to
        be translated *from*, if not English).

        Throw a 404 if it's not in rosetta_settings.ROSETTA_LANGUAGES.
        """
        ref_lang = self._request_request('ref_lang', 'msgid')
        if ref_lang != 'msgid':
            allowed_languages = {l[0] for l in rosetta_settings.ROSETTA_LANGUAGES}
            if ref_lang not in allowed_languages:
                raise Http404
        return ref_lang

    @cached_property
    def ref_lang_po_file(self):
        """Return a parsed .po file object for the "reference language", if one
        exists, otherwise None.
        """
        ref_pofile = None
        if rosetta_settings.ENABLE_REFLANG and self.ref_lang != 'msgid':
            replacement = '{separator}locale{separator}{ref_lang}'.format(
                separator=os.sep,
                ref_lang=self.ref_lang
            )
            pattern = '\{separator}locale\{separator}[a-z]{{2}}'.format(separator=os.sep)
            ref_fn = re.sub(pattern, replacement, self.po_file_path,)
            try:
                ref_pofile = pofile(ref_fn)
            except IOError:
                # there's a syntax error in the PO file and polib can't
                # open it. Let's just do nothing and thus display msgids.
                # XXX: :-/
                pass
        return ref_pofile

    @cached_property
    def msg_filter(self):
        """Validate/return msg_filter from request (e.g. 'fuzzy', 'untranslated'),
        or a default.

        If a query is also specified in the request, then return None.
        """
        if self.query:
            msg_filter = None
        else:
            msg_filter = self._request_request('msg_filter', 'all')
            available_msg_filters = {'untranslated', 'translated', 'fuzzy', 'all'}
            if msg_filter not in available_msg_filters:
                msg_filter = 'all'
        return msg_filter

    @cached_property
    def query(self):
        """Strip and return the query (for searching the catalog) from the
        request, or None.
        """
        return self._request_request('query', '').strip() or None

    def get_entries(self):
        """Return a list of the entries (messages) that would be part of the
        current "view"; that is, all of the ones from this .po file matching the
        current query or msg_filter.
        """
        if self.query:
            # Scenario #1: terms matching a search query
            rx = re.compile(re.escape(self.query), re.IGNORECASE)

            def concat_entry(e):
                return (six.text_type(e.msgstr) +
                        six.text_type(e.msgid) +
                        six.text_type(e.msgctxt) +
                        six.text_type(e.comment) +
                        u''.join([o[0] for o in e.occurrences]) +
                        six.text_type(e.msgid_plural) +
                        u''.join(e.msgstr_plural.values())
                        )

            entries = [e_ for e_ in self.po_file
                       if not e_.obsolete and rx.search(concat_entry(e_))]
        else:
            # Scenario #2: filtered list of messages
            if self.msg_filter == 'untranslated':
                entries = self.po_file.untranslated_entries()
            elif self.msg_filter == 'translated':
                entries = self.po_file.translated_entries()
            elif self.msg_filter == 'fuzzy':
                entries = [e_ for e_ in self.po_file.fuzzy_entries()
                           if not e_.obsolete]
            else:
                # ("all")
                entries = [e_ for e_ in self.po_file if not e_.obsolete]
        return entries


class TranslationFileDownload(RosettaFileLevelMixin, View):
    """Download a zip file for a specific catalog including both the raw (.po)
    and compiled (.mo) files, either as they exist on disk, or, if what's on
    disk is unwritable (permissions-wise), return what's in the cache.
    """
    http_method_names = [u'get']

    def get(self, request, *args, **kwargs):
        try:
            if len(self.po_file_path.split('/')) >= 5:
                offered_fn = '_'.join(self.po_file_path.split('/')[-5:])
            else:
                offered_fn = self.po_file_path.split('/')[-1]
            po_fn = str(self.po_file_path.split('/')[-1])
            mo_fn = str(po_fn.replace('.po', '.mo'))  # not so smart, huh
            zipdata = six.BytesIO()
            with zipfile.ZipFile(zipdata, mode="w") as zipf:
                zipf.writestr(po_fn, six.text_type(self.po_file).encode("utf8"))
                zipf.writestr(mo_fn, self.po_file.to_binary())
            zipdata.seek(0)

            response = HttpResponse(zipdata.read())
            filename = 'filename=%s.%s.zip' % (offered_fn, self.language_id)
            response['Content-Disposition'] = 'attachment; %s' % filename
            response['Content-Type'] = 'application/x-zip'
            return response
        except Exception:
            # XXX: should add a message!
            return HttpResponseRedirect(
                reverse('rosetta-file-list', kwargs={'po_filter': 'project'})
            )


@user_passes_test(lambda user: can_translate(user), LoginURL())
def translate_text(request):

    def translate(text, from_language, to_language, subscription_key):
        """
        This method does the heavy lifting of connecting to the translator API and fetching a response
        :param text: The source text to be translated
        :param from_language: The language of the source text
        :param to_language: The target language to translate the text into
        :param subscription_key: An API key that grants you access to the Azure translation service
        :return: Returns the response from the AZURE service as a python object. For more information about the
        response, please visit
        https://docs.microsoft.com/en-us/azure/cognitive-services/translator/reference/v3-0-translate?tabs=curl
        """

        AZURE_TRANSLATOR_HOST = 'https://api.cognitive.microsofttranslator.com'
        AZURE_TRANSLATOR_PATH = '/translate?api-version=3.0'

        headers = {
            'Ocp-Apim-Subscription-Key': subscription_key,
            'Content-type': 'application/json',
            'X-ClientTraceId': str(uuid.uuid4())
        }

        url_parameters = {
            "from": from_language,
            "to": to_language
        }

        request_data = [
            {"text": text}
        ]

        api_hostname = AZURE_TRANSLATOR_HOST + AZURE_TRANSLATOR_PATH
        r = requests.post(api_hostname, headers=headers, params=url_parameters, data=json.dumps(request_data))
        return json.loads(r.text)

    language_from = request.GET.get('from', None)
    language_to = request.GET.get('to', None)
    text = request.GET.get('text', None)

    if language_from == language_to:
        data = {'success': True, 'translation': text}
    else:
        # run the translation:
        AZURE_CLIENT_SECRET = getattr(settings, 'AZURE_CLIENT_SECRET', None)

        try:
            api_response = translate(text, language_from, language_to, AZURE_CLIENT_SECRET)

            # result will be a dict if there is an error, e.g.
            # {
            #   "success": false,
            #    "error": "Microsoft Translation API error: Error code 401000,
            #             The request is not authorized because credentials are missing or invalid."
            # }
            if isinstance(api_response, dict):
                api_error = api_response.get("error")
                error_code = api_error.get("code")
                error_message = api_error.get("message")
                data = {
                    'success': False,
                    'error': "Microsoft Translation API error: Error code {}, {}".format(error_code, error_message),
                }
            else:
                # response body will be of the form:
                # [
                #     {
                #         "translations":[
                #             {"text": "some chinese text that gave a build error on travis ci", "to": "zh-Hans"}
                #         ]
                #     }
                # ]
                # for more information, please visit
                # https://docs.microsoft.com/en-us/azure/cognitive-services/translator/reference/v3-0-translate?tabs=curl

                translations = api_response[0].get("translations")
                translated_text = translations[0].get("text")
                data = {
                    'success': True,
                    'translation': translated_text
                }
        # catch general connection exception in the requests framework
        except requests.exceptions.RequestException as err:
            data = {
                'success': False,
                'error': "Error connecting to Microsoft Translation Service: {0}".format(err),
            }

    return JsonResponse(data)


def urlencode_safe(query):
    return urlencode({k: force_bytes(v) for k, v in query.items()})
