Microsoft Translator V2 -- Python API
=====================================

:Version: 0.4
:Web: http://openlabs.co.in/
:keywords: Micrsoft Translator
:copyright: Openlabs Technologies & Consulting (P) LTD

.. image:: https://secure.travis-ci.org/openlabs/Microsoft-Translator-Python-API.png?branch=master
   :target: http://travis-ci.org/#!/openlabs/Microsoft-Translator-Python-API


This python API implements the Microsoft Translator services which can be used 
in web or client applications to perform language translation operations. The 
services support users who are not familiar with the default language of a page 
or application, or those desiring to communicate with people of a different 
language group.


Example Usage:
::

        >>> from microsofttranslator import Translator
        >>> translator = Translator('<Your Client ID>', '<Your Client Secret>')
        >>> print translator.translate("Hello", "pt")
        "Olá"

Registering your application
----------------------------

To register your application with Azure DataMarket, 
visit https://datamarket.azure.com/developer/applications/ using the
LiveID credentials from step 1, and click on “Register”. In the
“Register your application” dialog box, you can define your own
Client ID and Name. The redirect URI is not used for the Microsoft
Translator API. However, the redirect URI field is a mandatory field,
and you must provide a URI to obtain the access code. A description is
optional.

Take a note of the client ID and the client secret value.

Bugs and Development on Github
------------------------------

https://github.com/openlabs/Microsoft-Translator-Python-API
