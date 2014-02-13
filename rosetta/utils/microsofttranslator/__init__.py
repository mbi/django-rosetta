# -*- coding: utf-8 -*-
"""
    __init__

    A translator using the micrsoft translation engine documented here:

    http://msdn.microsoft.com/en-us/library/ff512419.aspx

    :copyright: © 2011 by Openlabs Technologies & Consulting (P) Limited
    :license: BSD, see LICENSE for more details.
"""

__all__ = ['Translator', 'TranslateApiException']

import requests
import warnings
import logging


class ArgumentOutOfRangeException(Exception):
    def __init__(self, message):
        self.message = message.replace('ArgumentOutOfRangeException: ', '')
        super(ArgumentOutOfRangeException, self).__init__(self.message)


class TranslateApiException(Exception):
    def __init__(self, message, *args):
        self.message = message.replace('TranslateApiException: ', '')
        super(TranslateApiException, self).__init__(self.message, *args)


class Translator(object):
    """Implements AJAX API for the Microsoft Translator service

    :param app_id: A string containing the Bing AppID. (Deprecated)
    """

    def __init__(self, client_id, client_secret,
            scope="http://api.microsofttranslator.com",
            grant_type="client_credentials", app_id=None, debug=False):
        """


        :param client_id: The client ID that you specified when you registered
                          your application with Azure DataMarket.
        :param client_secret: The client secret value that you obtained when
                              you registered your application with Azure
                              DataMarket.
        :param scope: Defaults to http://api.microsofttranslator.com
        ;param grant_type: Defaults to "client_credentials"
        :param app_id: Deprecated
        :param debug: If true, the logging level will be set to debug

        .. versionchanged: 0.4
            Bing AppID mechanism is deprecated and is no longer supported.
            See: http://msdn.microsoft.com/en-us/library/hh454950
        """
        if app_id is not None:
            warnings.warn("""app_id is deprected since v0.4.
            See: http://msdn.microsoft.com/en-us/library/hh454950
            """, DeprecationWarning, stacklevel=2)

        self.client_id = client_id
        self.client_secret = client_secret
        self.scope = scope
        self.grant_type = grant_type
        self.access_token = None
        self.debug = debug
        self.logger = logging.getLogger("microsofttranslator")
        if self.debug:
            self.logger.setLevel(level=logging.DEBUG)

    def get_access_token(self):
        """Bing AppID mechanism is deprecated and is no longer supported.
        As mentioned above, you must obtain an access token to use the
        Microsoft Translator API. The access token is more secure, OAuth
        standard compliant, and more flexible. Users who are using Bing AppID
        are strongly recommended to get an access token as soon as possible.

        .. note::
            The value of access token can be used for subsequent calls to the
            Microsoft Translator API. The access token expires after 10
            minutes. It is always better to check elapsed time between time at
            which token issued and current time. If elapsed time exceeds 10
            minute time period renew access token by following obtaining
            access token procedure.

        :return: The access token to be used with subsequent requests
        """
        args = {
            'client_id': self.client_id,
            'client_secret': self.client_secret,
            'scope': self.scope,
            'grant_type': self.grant_type
        }
        response = requests.post(
            'https://datamarket.accesscontrol.windows.net/v2/OAuth2-13',
            data=args
        ).json()

        self.logger.debug(response)

        if "error" in response:
            raise TranslateApiException(
                response.get('error_description', 'No Error Description'),
                response.get('error', 'Unknown Error')
            )
        return response['access_token']

    def call(self, url, params):
        """Calls the given url with the params urlencoded
        """
        if not self.access_token:
            self.access_token = self.get_access_token()

        resp = requests.get(
            "%s" % url,
            params=params,
            headers={'Authorization': 'Bearer %s' % self.access_token}
        )
        resp.encoding = 'UTF-8-sig'
        rv = resp.json()
        #rv = json.loads(response.decode("UTF-8-sig"))

        if isinstance(rv, str) and \
                rv.startswith("ArgumentOutOfRangeException"):
            raise ArgumentOutOfRangeException(rv)

        if isinstance(rv, str) and \
                rv.startswith("TranslateApiException"):
            raise TranslateApiException(rv)

        return rv

    def translate(self, text, to_lang, from_lang=None,
            content_type='text/plain', category='general'):
        """Translates a text string from one language to another.

        :param text: A string representing the text to translate.
        :param to_lang: A string representing the language code to
            translate the text into.
        :param from_lang: A string representing the language code of the
            translation text. If left None the response will include the
            result of language auto-detection. (Default: None)
        :param content_type: The format of the text being translated.
            The supported formats are "text/plain" and "text/html". Any HTML
            needs to be well-formed.
        :param category: The category of the text to translate. The only
            supported category is "general".
        """
        params = {
            'text': text.encode('utf8'),
            'to': to_lang,
            'contentType': content_type,
            'category': category,
            }
        if from_lang is not None:
            params['from'] = from_lang
        return self.call(
            "http://api.microsofttranslator.com/V2/Ajax.svc/Translate",
            params)

    def translate_array(self, texts, to_lang, from_lang=None, **options):
        """Translates an array of text strings from one language to another.

        :param texts: A list containing texts for translation.
        :param to_lang: A string representing the language code to
            translate the text into.
        :param from_lang: A string representing the language code of the
            translation text. If left None the response will include the
            result of language auto-detection. (Default: None)
        :param options: A TranslateOptions element containing the values below.
            They are all optional and default to the most common settings.

                Category: A string containing the category (domain) of the
                    translation. Defaults to "general".
                ContentType: The format of the text being translated. The
                    supported formats are "text/plain" and "text/html". Any
                    HTML needs to be well-formed.
                Uri: A string containing the content location of this
                    translation.
                User: A string used to track the originator of the submission.
                State: User state to help correlate request and response. The
                    same contents will be returned in the response.
        """
        options = {
            'Category': "general",
            'Contenttype': "text/plain",
            'Uri': '',
            'User': 'default',
            'State': ''
            }.update(options)
        params = {
            'texts': json.dumps(texts),
            'to': to_lang,
            'options': json.dumps(options),
            }
        if from_lang is not None:
            params['from'] = from_lang

        return self.call(
                "http://api.microsofttranslator.com/V2/Ajax.svc/TranslateArray",
                params)
