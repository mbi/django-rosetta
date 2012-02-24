{% load rosetta %}

google.setOnLoadCallback(function() {
    $('.location a').show().toggle(function() {
        $('.hide', $(this).parent()).show();
    }, function() {
        $('.hide', $(this).parent()).hide();
    });

{% if ENABLE_TRANSLATION_SUGGESTIONS and BING_APP_ID %}    
    $('a.suggest').click(function(e){
        e.preventDefault();
        var a = $(this);
        var str = a.html();
        var orig = $('.original .message', a.parents('tr')).html();
        var trans=$('textarea',a.parent());
        var sourceLang = '{{ MESSAGES_SOURCE_LANGUAGE_CODE }}';
        var destLang = '{{ rosetta_i18n_lang_code }}';
        var app_id = '{{ BING_APP_ID }}';
        var apiUrl = "http://api.microsofttranslator.com/V2/Ajax.svc/Translate";

        orig = unescape(orig).replace(/<br\s?\/?>/g,'\n').replace(/<code>/,'').replace(/<\/code>/g,'').replace(/&gt;/g,'>').replace(/&lt;/g,'<');
        a.attr('class','suggesting').html('...');
        window.onTranslationComplete = function(resp) {
            trans.val(unescape(resp).replace(/&#39;/g,'\'').replace(/&quot;/g,'"').replace(/%\s+(\([^\)]+\))\s*s/g,' %$1s '));
            a.hide();
        };
        window.onTranslationError = function(response){
            a.text(response);
        };
        var apiData = {
            onerror: 'onTranslationError',
            appid: app_id,
            from: sourceLang,
            to: destLang,
            oncomplete: "onTranslationComplete",
            text: orig
        };
        $.ajax({
            url: apiUrl,
            data: apiData,
            dataType: 'jsonp'});
    });
{% endif %}

    $('td.plural').each(function(i) {
        var td = $(this), trY = parseInt(td.closest('tr').offset().top);
        $('textarea', $(this).closest('tr')).each(function(j) {
            var textareaY=  parseInt($(this).offset().top) - trY;
            $($('.part',td).get(j)).css('top',textareaY + 'px');
        });
    });
    
    $('.translation textarea').blur(function() {
        if($(this).val()) {
            $('.alert', $(this).parents('tr')).remove();
            var RX = /%(?:\([^\s\)]*\))?[sdf]/g,
                origs=$('.original', $(this).parents('tr')).html().match(RX),
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
    });

    $('.translation textarea').eq(0).focus();
    
});
