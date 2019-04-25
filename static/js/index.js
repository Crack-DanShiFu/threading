$(document).ready(function () {
    $('#myTab li:eq(0) a').tab('show');
    $('.single_thread .btn-primary').attr('disabled', true);
    $('.multi_threading .btn-primary').attr('disabled', true);


    $('.single_thread select[name="cycle-section"]').change(function (val) {
        if ($('.single_thread select[name="cycle-section"]').val() == '') {
            $('.single_thread .btn-primary').attr('disabled', true);
        } else {
            $('.single_thread .btn-primary').attr('disabled', false);
        }
        $('.single_thread .progress-bar').css('width', 0 + '%')
        $.ajax({
            url: '/cycleSession',
            type: 'POST',
            dataType: 'json',
            data: {'cycle': $('.single_thread select[name="cycle-section"]').val()},
            success: function (data) {
            }
        });
    })

    $('.single_thread .btn-primary').click(function () {
        $('.single_thread .progress-bar').css('width', 0 + '%')
        $(document).ready(function () {
            $('.time').text('准备中')
            namespace = '/single_thread';
            var socket = io.connect(location.protocol + '//' + document.domain + ':' + location.port + namespace);
            socket.on('server_response',
                function (res) {
                    $('.single_thread .time').text('运行中')
                    $('.single_thread .progress-bar').css('width', res['count'] + '%')
                    $('.single_thread .percent').text(res['count'] + '%完成')
                });

            socket.on('run_time',
                function (res) {
                    $('.single_thread .time').text(res['time'] + ' s')
                });
        });
    })

    $('.multi_threading select[name="thread-section"]').change(function (val) {
        if ($('.multi_threading select[name="thread-section"]').val() != "" &&
            $('.multi_threading select[name="calculate-section"]').val() != "") {
            $('.multi_threading .btn-primary').attr('disabled', false);
            $.ajax({
                url: '/sumThreadSession',
                type: 'POST',
                dataType: 'json',
                data: {
                    'sumThreadSession': $('.multi_threading select[name="thread-section"]').val(),
                    'calculate_num': $('.multi_threading select[name="calculate-section"]').val()
                },
                success: function (data) {
                }
            });


        } else {
            $('.multi_threading .btn-primary').attr('disabled', true);

        }


        $('.multi_threading .multi_threading_progress').empty()
        var sum_of_progress = parseInt($('.multi_threading select[name="thread-section"]').val())
        for (let i = 0; i < sum_of_progress + 1; i++) {

            $('.multi_threading .multi_threading_progress').append('                <div class="progress progress-striped active">\n' +
                '                        <div class="progress-bar progress-bar-success" role="progressbar"\n' +
                '                             aria-valuemin="0" aria-valuemax="100"\n' +
                '                             style="width: 0%;">\n' +
                '                        </div>\n' +
                '                    </div>\n' +
                '<span class="time">0s</span>\n' +

                '                    <span class="num">完成0个</span>')
        }
    })

    $('.multi_threading select[name="calculate-section"]').change(function (val) {
        if ($('.multi_threading select[name="thread-section"]').val() != "" &&
            $('.multi_threading select[name="calculate-section"]').val() != "") {
            $('.multi_threading .btn-primary').attr('disabled', false);
            $.ajax({
                url: '/sumThreadSession',
                type: 'POST',
                dataType: 'json',
                data: {
                    'sumThreadSession': $('.multi_threading select[name="thread-section"]').val(),
                    'calculate_num': $('.multi_threading select[name="calculate-section"]').val()
                },
                success: function (data) {

                }
            });

        } else {
            $('.multi_threading .btn-primary').attr('disabled', true);
        }
    })


    $('.multi_threading .btn-primary').click(function () {
            var sum_of_progress = parseInt($('.multi_threading select[name="thread-section"]').val())
            var sum_of_calculate = parseInt($('.multi_threading select[name="calculate-section"]').val())
            var list = {'num': []}
            var allNum = 0
            for (let i = 0; i < sum_of_progress; i++) {
                list['num'].push(0)
            }
            $(document).ready(function () {
                namespace = '/multi_thread';
                all_time = 0
                var socket = io.connect(location.protocol + '//' + document.domain + ':' + location.port + namespace);
                socket.on('server_response',
                    function (res) {
                        num = res['num']
                        i = res['i']
                        list['num'][i] += 1
                        allNum += 1
                        $('.multi_threading .progress-bar:eq(' + i + ')').css('width', list['num'][i] + '%')
                        $('.multi_threading .num:eq(' + i + ')').text('线程' + i + '完成运行' + list['num'][i] + '个')
                        $('.multi_threading .num:eq(' + sum_of_progress + ')').text('总进度完成运行' + allNum + '个')
                        $('.multi_threading .progress-bar:eq(' + sum_of_progress + ')').css('width', (allNum * 100 / sum_of_calculate) + '%')

                    }
                );
                socket.on('run_time',
                    function (res) {
                        i = res['i']
                        all_time += res['time']
                        $('.multi_threading .time:eq(' + i + ')').text('用时' + res['time'] + 's  ')
                        $('.multi_threading .time:eq(' + sum_of_progress + ')').text('总用时' + all_time + 's  ')
                    });
            });
        }
    )

    $('.supply_consumer select[name="supply_section"]').change(function () {
        $.ajax({
            url: '/supply_source',
            type: 'POST',
            dataType: 'json',
            data: {
                'supply_source_speed': $('.supply_consumer select[name="supply_section"]').val(),
            },
            success: function (data) {

            }
        });
    })
    $('.supply_consumer select[name="consumer_section"]').change(function () {
        $.ajax({
            url: '/consumer_source',
            type: 'POST',
            dataType: 'json',
            data: {
                'consumer_source_speed': $('.supply_consumer select[name="consumer_section"]').val(),
            },
            success: function (data) {

            }
        });
    })

    $('.supply_consumer .btn-primary').click(function () {
        $.ajax({
            url: '/supply_source',
            type: 'POST',
            dataType: 'json',
            data: {
                'supply_source_speed': $('.supply_consumer select[name="supply_section"]').val(),
            },
            success: function (data) {

            }
        });

        $.ajax({
            url: '/consumer_source',
            type: 'POST',
            dataType: 'json',
            data: {
                'consumer_source_speed': $('.supply_consumer select[name="consumer_section"]').val(),
            },
            success: function (data) {

            }
        });
        namespace = '/supply_consumer';
        var socket = io.connect(location.protocol + '//' + document.domain + ':' + location.port + namespace);
        socket.on('q_size',
            function (res) {
                $('.supply_consumer .progress-bar').css('width', res['q_size'] + '%')
                $('.supply_consumer .source_num').text(res['q_size'] + '个')
            }
        );
    })

})




