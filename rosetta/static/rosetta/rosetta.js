$(document).ready({
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
