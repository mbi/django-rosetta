"use strict";

const rosetta_settings = JSON.parse(document.getElementById("rosetta-settings-js").textContent);

document.addEventListener("DOMContentLoaded", () => {
    // Get original html that corresponds to a given textarea containing the translation
    function originalForTextarea(textarea) {
        const textareasInCell = textarea.closest("td").querySelectorAll("textarea");
        const nth = Array.from(textareasInCell).indexOf(textarea) + 1;
        return textarea
            .closest("tr")
            .querySelector(".original")
            .querySelector(`.message, .part:nth-of-type(${nth})`).innerHTML;
    }

    // Common code for handling translation suggestions
    function suggest(translate) {
        document.querySelectorAll("a.suggest").forEach((a) => {
            a.addEventListener("click", (event) => {
                event.preventDefault();
                const textarea = a.previousElementSibling;
                const orig = originalForTextarea(textarea);
                a.classList.add("suggesting");
                a.textContent = "...";
                translate(
                    orig,
                    (translation) => {
                        textarea.value = translation;
                        textarea.dispatchEvent(new Event("input"));
                        textarea.dispatchEvent(new Event("change"));
                        textarea.dispatchEvent(new Event("blur"));
                        a.style.visibility = "hidden";
                    },
                    (error) => {
                        console.error("Rosetta translation suggestion error:", error);
                        let errorMsg;
                        if (error?.message) {
                            errorMsg = error.message;
                        } else if (error?.error) {
                            errorMsg = error.error;
                        } else if (typeof error === "object") {
                            errorMsg = JSON.stringify(error);
                        } else {
                            errorMsg = error || "Error loading translation";
                        }
                        a.textContent = String(errorMsg).trim().substring(0, 100);
                        alignPlurals();
                    },
                );
            });
        });
    }

    function jsonp(url, params, callback) {
        var callbackName = "rosetta_jsonp_callback_" + Math.random().toString(36).substr(2, 8);
        window[callbackName] = function (response) {
            callback(response);
            delete window[callbackName];
        };
        params.callback = callbackName;
        var script = document.createElement("script");
        script.src = `${url}?${new URLSearchParams(params).toString()}`;
        document.body.appendChild(script);
        script.onerror = function () {
            callback("Failed to load translation with jsonp request");
            delete window[callbackName];
        };
    }

    // Translation suggestions
    if (rosetta_settings.ENABLE_TRANSLATION_SUGGESTIONS) {
        if (rosetta_settings.server_auth_key) {
            suggest((orig, setTranslation, setError) => {
                const origUnescaped = unescape(orig)
                    .replace(/<br\s?\/?>/g, "\n")
                    .replace(/<code>/g, "")
                    .replace(/<\/code>/g, "")
                    .replace(/&gt;/g, ">")
                    .replace(/&lt;/g, "<");
                const params = new URLSearchParams({
                    from: rosetta_settings.MESSAGES_SOURCE_LANGUAGE_CODE,
                    to: rosetta_settings.rosetta_i18n_lang_code_normalized,
                    text: origUnescaped,
                });
                const url = `${rosetta_settings.translate_text_url}?${params.toString()}`;
                fetch(url)
                    .then((r) => r.json())
                    .then((data) => {
                        if (data.success) {
                            setTranslation(
                                unescape(data.translation)
                                    .replace(/&#39;/g, "'")
                                    .replace(/&quot;/g, '"')
                                    .replace(/%\s+(\([^)]+\))\s*s/g, " %$1s "),
                            );
                        } else {
                            setError(data);
                        }
                    })
                    .catch(setError);
            });
        } else if (rosetta_settings.YANDEX_TRANSLATE_KEY) {
            suggest((orig, setTranslation, setError) => {
                const apiUrl = "https://translate.yandex.net/api/v1.5/tr.json/translate";
                const destLangRoot = rosetta_settings.rosetta_i18n_lang_code.split("-")[0];
                const lang = rosetta_settings.MESSAGES_SOURCE_LANGUAGE_CODE + "-" + destLangRoot;
                const apiData = {
                    error: "onTranslationError",
                    success: "onTranslationComplete",
                    lang: lang,
                    key: rosetta_settings.YANDEX_TRANSLATE_KEY,
                    format: "html",
                    text: orig,
                };
                jsonp(apiUrl, apiData, (response) => {
                    if (response.code === 200) {
                        setTranslation(
                            response.text[0]
                                .replace(/< ?br>/g, "\n")
                                .replace(/< ?\/? ?code>/g, "")
                                .replace(/&lt;/g, "<")
                                .replace(/&gt;/g, ">"),
                        );
                    } else {
                        setError(response);
                    }
                });
            });
        }
    }

    // Make textarea height adapt to the contents
    function autofitTextarea(textarea) {
        textarea.style.height = "auto";
        textarea.style.height = textarea.scrollHeight + "px";
    }

    // If there are multiple textareas for plurals then align the originals vertically with the textareas
    function alignPlurals() {
        document.querySelectorAll(".results td.plural").forEach((td) => {
            const tr = td.closest("tr");
            const trY = tr.getBoundingClientRect().top + window.scrollY;
            tr.querySelectorAll("textarea").forEach((textarea, i) => {
                const part = td.querySelectorAll(".part")[i];
                if (part) {
                    const textareaY = textarea.getBoundingClientRect().top + window.scrollY - trY;
                    part.style.top = textareaY + "px";
                }
            });
        });
    }

    // Show warning if the variables in the original and the translation don't match
    function validateTranslation(textarea) {
        const orig = originalForTextarea(textarea);
        const variablePattern = /%(?:\([^\s)]*\))?[sdf]|\{[^\s}]*\}/g;
        const origVars = orig.match(variablePattern) || [];
        const transVars = textarea.value.match(variablePattern) || [];
        const everyOrigVarUsed = origVars.every((origVar) => transVars.includes(origVar));
        const onlyValidVarsUsed = transVars.every((transVar) => origVars.includes(transVar));
        const valid = everyOrigVarUsed && onlyValidVarsUsed;
        textarea.previousElementSibling.classList.toggle("hidden", valid);
    }

    // Select all the textareas that are used for translations
    const textareas = document.querySelectorAll(".translation textarea");

    // For each translation field textarea
    textareas.forEach((textarea) => {
        // On page load make textarea height adapt to its contents
        autofitTextarea(textarea);

        // On page load show warnings for unmatched variables in translations
        validateTranslation(textarea);

        // On input
        textarea.addEventListener("input", () => {
            // Make textarea height adapt to its contents
            autofitTextarea(textarea);

            // If there are multiple textareas for plurals then align the originals vertically with the textareas
            alignPlurals();

            // Once users start editing the translation untick the fuzzy checkbox automatically
            textarea.closest("tr").querySelector('td.c input[type="checkbox"]').checked = false;
        });

        // On blur show warnings for unmatched variables in translations
        textarea.addEventListener("blur", () => validateTranslation(textarea));
    });

    // On window resize make textarea height adapt to their contents
    window.addEventListener("resize", () => textareas.forEach(autofitTextarea), { passive: true });

    // On page load if there are multiple textareas in a cell for plurals then align the originals vertically with them
    alignPlurals();

    // Reload page when changing ref-language
    document.getElementById("ref-language-selector")?.addEventListener("change", function () {
        window.location.href = this.value;
    });

    // Toggle fuzzy state for all entries on the current page
    document.getElementById("action-toggle")?.addEventListener("change", function () {
        const checkboxes = document.querySelectorAll('tbody td.c input[type="checkbox"]');
        checkboxes.forEach((checkbox) => (checkbox.checked = this.checked));
    });

    // Toggle additional locations that are initially hidden
    document.querySelectorAll(".location a").forEach((link) => {
        link.addEventListener("click", (event) => {
            event.preventDefault();
            const prevText = link.innerText;
            link.innerText = link.dataset.prevText;
            link.dataset.prevText = prevText;
            link.parentElement.querySelectorAll(".hide").forEach((loc) => {
                const hidden = loc.style.display === "none" || loc.style.display === "";
                loc.style.display = hidden ? "block" : "none";
            });
        });
    });

    // Warn about any unsaved changes before navigating away from the page
    const form = document.querySelector("form.results");
    function formToJsonString() {
        const obj = {};
        new FormData(form).forEach((value, key) => (obj[key] = value));
        return JSON.stringify(obj);
    }
    if (form) {
        const initialDataJson = formToJsonString();
        let isSubmitting = false;
        form.addEventListener("submit", () => (isSubmitting = true));
        window.addEventListener("beforeunload", (event) => {
            if (!isSubmitting && initialDataJson !== formToJsonString()) {
                event.preventDefault();
                event.returnValue = "";
            }
        });
    }
});
