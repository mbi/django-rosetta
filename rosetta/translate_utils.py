import json
import re
import uuid

import requests

from django.conf import settings


class TranslationException(Exception):
    pass


def translate(text, from_language, to_language):
    AZURE_CLIENT_SECRET = getattr(settings, "AZURE_CLIENT_SECRET", None)
    GOOGLE_APPLICATION_CREDENTIALS_PATH = getattr(
        settings, "GOOGLE_APPLICATION_CREDENTIALS_PATH", None
    )
    GOOGLE_PROJECT_ID = getattr(settings, "GOOGLE_PROJECT_ID", None)
    DEEPL_AUTH_KEY = getattr(settings, "DEEPL_AUTH_KEY", None)
    OPENAI_API_KEY = getattr(settings, "OPENAI_API_KEY", None)

    if DEEPL_AUTH_KEY:
        deepl_language_code = None
        DEEPL_LANGUAGES = getattr(settings, "DEEPL_LANGUAGES", None)
        if isinstance(DEEPL_LANGUAGES, dict):
            deepl_language_code = DEEPL_LANGUAGES.get(to_language, None)

        if deepl_language_code is None:
            deepl_language_code = to_language[:2].upper()

        return translate_by_deepl(
            text,
            deepl_language_code.upper(),
            DEEPL_AUTH_KEY,
        )

    elif AZURE_CLIENT_SECRET:
        return translate_by_azure(text, from_language, to_language, AZURE_CLIENT_SECRET)
    elif GOOGLE_APPLICATION_CREDENTIALS_PATH and GOOGLE_PROJECT_ID:
        return translate_by_google(
            text,
            from_language,
            to_language,
            GOOGLE_APPLICATION_CREDENTIALS_PATH,
            GOOGLE_PROJECT_ID,
        )
    elif OPENAI_API_KEY:
        return translate_by_openai(text, from_language, to_language, OPENAI_API_KEY)
    else:
        raise TranslationException("No translation API service is configured.")


def format_text_to_deepl(text):
    pattern = r"%\((\w+)\)(\w)"

    def replace_variable(match):
        # Our pattern will always catch 2 groups, the first group being '%('
        # Second group being ')d' or ')s'
        variable = match.group(1)
        type_specifier = match.group(2)
        if variable and type_specifier:
            return f'<var type="{type_specifier}">{variable}</var>'
        else:
            raise TranslationException("Badly formatted variable in translation")

    return re.sub(pattern, replace_variable, text)


def format_text_from_deepl(text):
    for g in re.finditer(
        r'.*?<var type="(?P<type>[rsd])">(?P<variable>[0-9a-zA-Z_]+)</var>.*?', text
    ):
        t, v = g.groups()
        text = text.replace(f'<var type="{t}">{v}</var>', f"%({v}){t}")
    return text


def translate_by_deepl(text, to_language, auth_key):
    """
    This method connects to the translator Deepl API and fetches a response with translations.
    :param text: The source text to be translated
    :param to_language: The target language to translate the text into
    Wraps variables in <var></var> tags and instructs Deepl not to translate those.
    Then from Deepl response, converts back these tags to django variable syntax.
    %(name)s becomes <var type="s">name</var> and back to %(name)s in the response text.
    :return: Returns the response from the Deepl as a python object.
    """
    if auth_key.lower().endswith(":fx"):
        endpoint = "https://api-free.deepl.com"
    else:
        endpoint = "https://api.deepl.com"

    r = requests.post(
        f"{endpoint}/v2/translate",
        headers={"Authorization": f"DeepL-Auth-Key {auth_key}"},
        data={
            "tag_handling": "xml",
            "ignore_tags": "var",
            "target_lang": to_language.upper(),
            "text": format_text_to_deepl(text),
        },
    )
    if r.status_code != 200:
        raise TranslationException(
            f"Deepl response is {r.status_code}. Please check your API key or try again later."
        )

    try:
        return format_text_from_deepl(r.json().get("translations")[0].get("text"))
    except Exception:
        raise TranslationException("Deepl returned a non-JSON or unexpected response.")


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

    AZURE_TRANSLATOR_HOST = "https://api.cognitive.microsofttranslator.com"
    AZURE_TRANSLATOR_PATH = "/translate?api-version=3.0"

    headers = {
        "Ocp-Apim-Subscription-Key": subscription_key,
        "Content-type": "application/json",
        "X-ClientTraceId": str(uuid.uuid4()),
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
    parent = "projects/{}/locations/{}".format(project_id, "global")
    try:
        api_response = client.translate_text(
            request=dict(
                parent=parent,
                contents=[text],
                mime_type="text/plain",
                source_language_code=input_language,
                target_language_code=output_language.split(".", 1)[0],
            )
        )
    except Exception as e:
        raise TranslationException("Google API error: {}".format(e))
    else:
        return str(api_response.translations[0].translated_text)


def translate_by_openai(
    text: str, from_language: str, to_language: str, api_key: str
) -> str:
    """
    Translate text using OpenAI's GPT-3.5-turbo-instruct engine.
    param text: The text to translate.
    param from_language: The language of the text.
    param to_language: The language to translate the text into.
    param api_key: The OpenAI API key.
    return: The translated text.
    """
    from openai import OpenAI

    client = OpenAI(api_key=api_key)

    OPENAI_BASE_URL = getattr(settings, "OPENAI_BASE_URL", None)
    OPENAI_MODEL = getattr(settings, "OPENAI_MODEL", None)
    prompt_template = getattr(
        settings,
        "OPENAI_PROMPT_TEMPLATE",
        "Translate the following text from {from_language} to {to_language}:\n\n{text}",
    )

    if OPENAI_BASE_URL:
        client.base_url = OPENAI_BASE_URL

    prompt = prompt_template.format(
        **{"from_language": from_language, "to_language": to_language, "text": text}
    )

    llm_model = OPENAI_MODEL or "gpt-3.5-turbo-instruct"
    try:
        response = client.completions.create(model=llm_model, prompt=prompt)
        translation = response.choices[0].text.strip()
    except Exception as e:
        raise TranslationException("OpenAI API error: {}".format(e))

    return translation
