(function($) {
    $(document).ready(function(){
        var loading = $('#loading'),
            apiUrl = '/api/v1/users';

        $.getJSON(apiUrl, function(result) {
            var dropdown = $('#user_id');

            $.each(result, function() {
                dropdown.append($('<option />', {'val': this.user_id, 'text': this.name}));
            });

            dropdown.show();
            loading.hide();
        });
        $('#user_id').change(function(){
            var $selectedUser = $('#user_id').val(),
                $chartDiv = $('#chart_div');

            if($selectedUser) {
                loading.show();
                $chartDiv.hide();

                $.getJSON('/api/v1/mean_time_month/'+$selectedUser, function(result) {
                    var data = new google.visualization.DataTable(),
                        options = {
                            hAxis: {
                                title: 'Month'
                            },
                            vAxis: {
                                title: 'Mean presence time',
                                minValue: [0, 0, 0]
                            },
                        },
                        formatter = new google.visualization.DateFormat({pattern: 'HH:mm:ss'}),
                        chart = new google.visualization.ColumnChart($chartDiv[0]);

                    data.addColumn('string', 'Month');
                    data.addColumn('timeofday', 'Mean time (h:m:s)');
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
