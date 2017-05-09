(function($) {
    $(document).ready(function(){
        var $loading = $('#loading'),
            $chartDiv = $('#chart_div');

        $.getJSON("/api/v1/users", function(result) {
            var dropdown = $("#user_id");
            $.each(result, function(item) {
                dropdown.append($("<option />").val(this.user_id).text(this.name));
            });
            dropdown.show();
            $loading.hide();
        });
        $('#user_id').change(function(){
            var selected_user = $("#user_id").val();

            if(selected_user) {
                $loading.show();
                $chartDiv.hide();
                $.getJSON("/api/v1/presence_weekday/"+selected_user, function(result) {
                    var data = google.visualization.arrayToDataTable(result);
                    var options = {};
                    $chartDiv.show();
                    $loading.hide();
                    var chart = new google.visualization.PieChart($chartDiv[0]);
                    chart.draw(data, options);
                });
            } else {
                $chartDiv.hide();
            }
        });
    });
})(jQuery);
