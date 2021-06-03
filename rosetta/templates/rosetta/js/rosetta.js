{% load rosetta %}

$(document).ready(function() {

    $('.location a').show().toggle(function() {
        $('.hide', $(this).parent()).show();
    }, function() {
        $('.hide', $(this).parent()).hide();
    });


{% if rosetta_settings.ENABLE_TRANSLATION_SUGGESTIONS %}
    {% if rosetta_settings.DEEPL_AUTH_KEY %}

        $('a.suggest').click(function(e){
            e.preventDefault();
            var a = $(this);
            var str = a.html();
            var orig = $('.original .message', a.parents('tr')).html();
            var trans=$('textarea',a.parent());
            var apiUrl = "https://api-free.deepl.com/v2/translate";
            {% if deepl_language_code %}
                var destLangRoot = '{{ deepl_language_code }}';
            {% else %}
                var destLangRoot = '{{ rosetta_i18n_lang_code_normalized }}'.substring(0, 2);
            {% endif %}
            var sourceLang = '{{ rosetta_settings.MESSAGES_SOURCE_LANGUAGE_CODE }}'.substring(0, 2);
            let authKey = '{{ rosetta_settings.DEEPL_AUTH_KEY }}:fx';

            a.attr('class','suggesting').html('...');
            fetch(apiUrl, {
                method: 'POST',
                headers: {
                    "Content-Type": "application/x-www-form-urlencoded"
                },
                body: `auth_key=${authKey}&text=${orig}&source_lang=${sourceLang}&target_lang=${destLangRoot}`
                }).then(response => {
                    if(response.ok) {
                        return response.json();
                    }
                }).then(data => {
                    trans.val(data.translations[0].text.replace(/<br>/g, '\n').replace(/<\/?code>/g, '').replace(/&lt;/g, '<').replace(/&gt;/g, '>'));
                })
                .catch(error => console.log(error));
        });
    {% elif rosetta_settings.AZURE_CLIENT_SECRET or rosetta_settings.GOOGLE_APPLICATION_CREDENTIALS_PATH %}
    $('a.suggest').click(function(e){
        e.preventDefault();
        var a = $(this);
        var str = a.html();
        var orig = $('.original .message', a.parents('tr')).html();
        var trans=$('textarea',a.parent());
        var sourceLang = '{{ rosetta_settings.MESSAGES_SOURCE_LANGUAGE_CODE }}';
        var destLang = '{{ rosetta_i18n_lang_code_normalized }}';

        orig = unescape(orig).replace(/<br\s?\/?>/g,'\n').replace(/<code>/,'').replace(/<\/code>/g,'').replace(/&gt;/g,'>').replace(/&lt;/g,'<');
        a.attr('class','suggesting').html('...');

        $.getJSON("{% url 'rosetta.translate_text' %}", {
                from: sourceLang,
                to: destLang,
                text: orig
            },
            function(data) {
                if (data.success){
                    trans.val(unescape(data.translation).replace(/&#39;/g,'\'').replace(/&quot;/g,'"').replace(/%\s+(\([^\)]+\))\s*s/g,' %$1s '));
                    a.hide();
                } else {
                    a.text(data.error);
                }
            }
        );
    });
   {% elif rosetta_settings.YANDEX_TRANSLATE_KEY %}
    $('a.suggest').click(function(e){
        e.preventDefault();
        var a = $(this);
        var str = a.html();
        var orig = $('.original .message', a.parents('tr')).html();
        var trans=$('textarea',a.parent());
        var apiUrl = "https://translate.yandex.net/api/v1.5/tr.json/translate";
        var destLangRoot = '{{ rosetta_i18n_lang_code }}'.split('-')[0];
        var lang = '{{ rosetta_settings.MESSAGES_SOURCE_LANGUAGE_CODE }}-' + destLangRoot;

        a.attr('class','suggesting').html('...');

        var apiData = {
            error: 'onTranslationError',
            success: 'onTranslationComplete',
            lang: lang,
            key: '{{ rosetta_settings.YANDEX_TRANSLATE_KEY }}',
            format: 'html',
            text: orig
        };

        $.ajax({
            url: apiUrl,
            data: apiData,
            dataType: 'jsonp',
            success: function(response) {
                if (response.code == 200) {
                    trans.val(response.text[0].replace(/<br>/g, '\n').replace(/<\/?code>/g, '').replace(/&lt;/g, '<').replace(/&gt;/g, '>'));
                    a.hide();
                } else {
                    a.text(response);
                }
            },
            error: function(response) {
                a.text(response);
            }
        });
    });
   {% endif %}
{% endif %}

    $('td.plural').each(function(i) {
        var td = $(this), trY = parseInt(td.closest('tr').offset().top);
        $('textarea', $(this).closest('tr')).each(function(j) {
            var textareaY=  parseInt($(this).offset().top) - trY;
            $($('.part',td).get(j)).css('top',textareaY + 'px');
        });
    });

    $('.translation textarea')

    .blur(function() {
        if($(this).val()) {
            $('.alert', $(this).parents('tr')).remove();
            var RX = /%(?:\([^\s\)]*\))?[sdf]|\{[\w\d_]+?\}/g,
                origs=$(this).parents('tr').find('.original>.message').html().match(RX),
                trads=$(this).val().match(RX),
                error = $('<span class="alert">Unmatched variables</span>');

            if (origs && trads) {
                for (var i = trads.length; i--;){
                    var key = trads[i];
                    if (-1 == $.inArray(key, origs)) {
                        $(this).before(error)
                        return false;
                    }
                }
                return true;
            } else {
                if (!(origs === null && trads === null)) {
                    $(this).before(error);
                    return false;
                }
            }
            return true;
        }
    })

    .keyup(function () {
        var cb = $(this).parents('tr').find('td.c input[type="checkbox"]');
        if(cb.is(':checked')){
            cb[0].checked = false;
            cb.removeAttr( 'checked')
        }

    })

    .eq(0).focus();

    $('#action-toggle').change(function(){
        jQuery('tbody td.c input[type="checkbox"]').each(function(i, e) {
            if($('#action-toggle').is(':checked')) {
                $(e).attr('checked', 'checked');
            } else {
                $(e).removeAttr('checked');
            }
        });
    });

});
