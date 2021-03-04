import json
import uuid

from django.conf import settings

import requests


class TranslationException(Exception):
    pass


def translate(text, from_language, to_language):
    AZURE_CLIENT_SECRET = getattr(settings, 'AZURE_CLIENT_SECRET', None)
    GOOGLE_APPLICATION_CREDENTIALS_PATH = getattr(
        settings, 'GOOGLE_APPLICATION_CREDENTIALS_PATH', None
    )
    GOOGLE_PROJECT_ID = getattr(settings, 'GOOGLE_PROJECT_ID', None)

    if AZURE_CLIENT_SECRET:
        return translate_by_azure(text, from_language, to_language, AZURE_CLIENT_SECRET)
    elif GOOGLE_APPLICATION_CREDENTIALS_PATH and GOOGLE_PROJECT_ID:
        return translate_by_google(
            text,
            from_language,
            to_language,
            GOOGLE_APPLICATION_CREDENTIALS_PATH,
            GOOGLE_PROJECT_ID,
        )
    else:
        raise TranslationException('No translation API service is configured.')


def translate_by_azure(text, from_language, to_language, subscription_key):
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
        'X-ClientTraceId': str(uuid.uuid4()),
    }

    url_parameters = {"from": from_language, "to": to_language}

    request_data = [{"text": text}]

    api_hostname = AZURE_TRANSLATOR_HOST + AZURE_TRANSLATOR_PATH
    r = requests.post(
        api_hostname,
        headers=headers,
        params=url_parameters,
        data=json.dumps(request_data),
    )
    api_response = json.loads(r.text)

    try:
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

            raise TranslationException(
                "Microsoft Translation API error: Error code {}, {}".format(
                    error_code, error_message
                )
            )
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

            return translated_text
    except requests.exceptions.RequestException as err:
        raise TranslationException(
            "Error connecting to Microsoft Translation Service: {0}".format(err)
        )


def translate_by_google(
    text, input_language, output_language, creadentials_path, project_id
):
    from google.cloud import translate as google_translate

    client = google_translate.TranslationServiceClient.from_service_account_json(
        creadentials_path
    )
    parent = "projects/{}/locations/{}".format(project_id, 'global')
    try:
        api_response = client.translate_text(
            request=dict(
                parent=parent,
                contents=[text],
                mime_type='text/plain',
                source_language_code=input_language,
                target_language_code=output_language.split('.', 1)[0],
            )
        )
    except Exception as e:
        raise TranslationException('Google API error: {}'.format(e))
    else:
        return str(api_response.translations[0].translated_text)
