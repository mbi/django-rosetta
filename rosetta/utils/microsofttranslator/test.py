# -*- coding: utf-8 -*-
"""
    test

    Test the translator

    :copyright: (c) 2012 by Openlabs Technologies & Consulting (P) Limited
    :license: BSD, see LICENSE for more details.
"""
import unittest
from rosetta.utils.microsofttranslator import Translator, TranslateApiException

client_id = "translaterpythonapi"
client_secret = "FLghnwW4LJmNgEG+EZkL8uE+wb7+6tkOS8eejHg3AaI="


class TestTranslator(unittest.TestCase):

    def test_translate(self):
        client = Translator(client_id, client_secret, debug=False)
        self.assertEqual(client.translate("hello", "pt"), u'Ol\xe1')

    def test_invalid_client_id(self):
        client = Translator("foo", "bar")
        with self.assertRaises(TranslateApiException):
            client.translate("hello", "pt")


def test_all():
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    suite.addTests(loader.loadTestsFromTestCase(TestTranslator))
    return suite


if __name__ == '__main__':
    unittest.main()
