(function() {
    $(function() {
        $('#user_id').change(function() {
            var getAvatarUrl = '/api/v1/user_avatar_url/' + $('#user_id').val(),
                $userAvatarElement = $('#user_avatar'),
                intranetBaseUrl = 'https://intranet.stxnext.pl';

            $.getJSON(getAvatarUrl, function(result) {
                $userAvatarElement.attr('src', intranetBaseUrl + result);
            }).fail(function() {
                $userAvatarElement.attr('src', '');
                window.alert('User details not found.');
            });
        });
    });
})(jQuery);
