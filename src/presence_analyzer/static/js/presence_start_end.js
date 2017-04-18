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

            var selectedUser = $("#user_id").val(),
                $chartDiv = $('#chart_div');

            if(selectedUser) {
                loading.show();
                $chartDiv.hide();

                $.getJSON("/api/v1/presence_start_end/"+selectedUser, function(result) {
                    var options, chart,
                        data = new google.visualization.DataTable(),
                        formatter = new google.visualization.DateFormat({pattern: 'HH:mm:ss'}),
                        options = {
                            hAxis: {title: 'Weekday'}
                        },
                        output = [];

                    $.each(result, function(day, times) {
                        output.push([
                            day,
                            new Date('1-1-1 ' + times['start']),
                            new Date('1-1-1 ' + times['end'])
                        ]);
                    });

                    data.addColumn('string', 'Weekday');
                    data.addColumn({ type: 'datetime', id: 'Start' });
                    data.addColumn({ type: 'datetime', id: 'End' });
                    data.addRows(output);

                    formatter.format(data, 1);
                    formatter.format(data, 2);

                    $chartDiv.show();
                    loading.hide();
                    chart = new google.visualization.Timeline($chartDiv[0]);
                    chart.draw(data, options);
                });
            }
        });
    });
})(jQuery);
