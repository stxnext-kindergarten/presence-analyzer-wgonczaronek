function parseInterval(value) {
    var result = new Date(1,1,1);
    result.setMilliseconds(value*1000);
    return result;
}

(function($) {
    $(document).ready(function(){
        var loading = $('#loading');
        $.getJSON("/api/v1/users", function(result) {
            var dropdown = $("#user_id");
            $.each(result, function(item) {
                dropdown.append($("<option />").val(this.user_id).text(this.name));
            });
            dropdown.show();
            loading.hide();
        });
        $('#user_id').change(function(){
            var $selectedUser = $("#user_id").val(),
                $chartDiv = $('#chart_div');
            if($selectedUser) {
                loading.show();
                $chartDiv.hide();
                $.getJSON("/api/v1/mean_time_weekday/"+$selectedUser, function(result) {
                    $.each(result, function(index, value) {
                        value[1] = parseInterval(value[1]);
                    }),
                    formatter = new google.visualization.DateFormat({pattern: 'HH:mm:ss'}),
                    data = new google.visualization.DataTable(),
                               options = {
                                   hAxis: {title: 'Weekday'}
                               },
                    chart = new google.visualization.ColumnChart($chartDiv[0]);

                    data.addColumn('string', 'Weekday');
                    data.addColumn('datetime', 'Mean time (h:m:s)');
                    data.addRows(result);
                    formatter.format(data, 1);

                    $chartDiv.show();
                    loading.hide();
                    chart.draw(data, options);
                });
            } else {
                $chartDiv.hide();
            }
        });
    });
})(jQuery);
