# -*- coding: utf-8 -*-
"""
    Microsoft translator API

    The Microsoft Translator services can be used in web or client
    applications to perform language translation operations. The services
    support users who are not familiar with the default language of a page or
    application, or those desiring to communicate with people of a different
    language group.

    This module implements the AJAX API for the Microsoft Translator service.

    An example::

        >>> from microsofttranslator import Translator
        >>> translator = Translator('<Your API Key>')
        >>> print translator.translate("Hello", "pt")
        "Olá"

    The documentation for the service can be obtained here:
    http://msdn.microsoft.com/en-us/library/ff512423.aspx

    The project is hosted on GitHub where your could fork the project or report
    issues. Visit https://github.com/openlabs/Microsoft-Translator-Python-API

    :copyright: © 2011 by Openlabs Technologies & Consulting (P) Limited
    :license: BSD, see LICENSE for more details.
"""
import os
from setuptools import setup

def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()

setup(
    name = "microsofttranslator",
    version = "0.4",
    packages = [
        'microsofttranslator',
        ],
    package_dir = {
        'microsofttranslator': '.'
        },
    author = "Openlabs Technologies & Consulting (P) Limited",
    author_email = "info@openlabs.co.in",
    description = "Microsoft Translator V2 - Python API",
    long_description = read('README.rst'),
    license = "BSD",
    keywords = "translation microsoft",
    url = "http://openlabs.co.in/",
    include_package_data = True,
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: BSD License",
        "Natural Language :: English",
        "Operating System :: OS Independent",
        "Topic :: Software Development :: Internationalization",
        "Topic :: Utilities"
    ],
    test_suite = "microsofttranslator.test.test_all",
    install_requires=[
        'requests >= 1.2.3',
    ]
)
