
var start_x = 0;
var start_y = 0;
var moving = 0;
var seq = 0;
var prev_x = 0;
var prev_y = 0;

function stop_motors() {
    var ajax_url = "/" + seq + "/move-stop/"
    seq++;

    $.ajax({
        type: "GET",
        cache: false,
        dataType: 'text',
        async: true,
        url: ajax_url
    });
    moving = 0;
}

function stop_medium_motor() {
    var ajax_url = "/" + seq + "/motor-stop/medium/"
    seq++;

    $.ajax({
        type: "GET",
        cache: false,
        dataType: 'text',
        async: true,
        url: ajax_url
    });
    return false;
}

function ajax_move_xy(x, y) {
    // console.log("FIRE ajax call with x,y " + x + "," + y)
    var ajax_url = "/" + seq + "/move-xy/" + x + "/" + y + "/"
    seq++;

    $.ajax({
        type: "GET",
        cache: false,
        dataType: 'text',
        async: true,
        url: ajax_url
    });
    moving = 1;
}

function ajax_log(msg) {
    var ajax_url = "/" + seq + "/log/" + msg + "/"
    seq++;

    $.ajax({
        type: "GET",
        cache: false,
        dataType: 'text',
        async: true,
        url: ajax_url
    });
}


// Prevent the page from scrolling on an iphone
// http://stackoverflow.com/questions/7768269/ipad-safari-disable-scrolling-and-bounce-effect
$(document).bind(
    'touchmove',
    function(e) {
        e.preventDefault();
    }
);

$(document).ready(function() {

    // Used the 'Restrict the inside circle to the outside circle' code
    var r = $('#joystick-wrapper').width()/2;
    var small_r = $('#joystick').width()/2;
    var origin_x = r - small_r;
    var origin_y = r - small_r;

    $("#medium-motor-speed").slider({
        min: 0,
        max: 100,
        step: 5,
        value: 50
    });

    $('#medium-motor-spin .CounterClockwise').bind('touchstart mousedown', function() {
        var power = $('#medium-motor-speed').slider("value")
        var ajax_url = "/" + seq + "/motor-start/medium/counter-clockwise/" + power + "/"
        seq++;

        $.ajax({
            type: "GET",
            cache: false,
            dataType: 'text',
            url: ajax_url
        });
        return false;
    });

    $('#medium-motor-spin .Clockwise').bind('touchstart mousedown', function() {
        var power = $('#medium-motor-speed').slider("value")
        var ajax_url = "/" + seq + "/motor-start/medium/clockwise/" + power + "/"
        seq++;

        $.ajax({
            type: "GET",
            cache: false,
            dataType: 'text',
            url: ajax_url
        });
        return false;
    });

    $('.medium').bind('touchend mouseup', function() {
        stop_medium_motor()
        return false;
    });

    $("div#joystick").draggable({
        revert: true,
        containment: "parent",
        create: function() {
            start_x = parseInt($(this).css("left"));
            start_y = parseInt($(this).css("top"));
            prev_x = start_x;
            prev_y = start_y;
        },
        drag: function(event, ui) {

            // Restrict the inside circle to the outside circle
            // http://stackoverflow.com/questions/26787996/containing-draggable-circle-to-a-larger-circle
            var x = ui.position.left - origin_x, y = ui.position.top - origin_y;
            var l = Math.sqrt(x*x + y*y);
            var l_in = Math.min(r - small_r, l);
            ui.position = {'left': Math.round(x/l*l_in) + origin_x, 'top': Math.round(y/l*l_in) + origin_y};

            // Get coordinates
            var x = ui.position.left - start_x
            var y = (ui.position.top - start_y) * -1
            var distance = 0;

            // If this is the initial touch then set the distance high so we'll move
            if (prev_x == start_x && prev_y == start_y) {
                distance = 99;
            } else {
                distance = Math.round(Math.sqrt(((x - prev_x) * (x - prev_x)) + ((y - prev_y) * (y - prev_y))));
            }

            // When you drag the joystick it can fire off a LOT of drag
            // events (one about every 8 ms), it ends up overwhelming the
            // web server on the EV3. It takes the EV3 ~55ms to process
            // one of these request so don't send one if the x,y coordinates
            // have only changed a tiny bit
            if (distance >= 10) {
                ajax_move_xy(x, y);
                prev_x = x;
                prev_y = y;
            }
        },
        stop: function() {
            if (moving) {
                stop_motors();
            }
            prev_x = start_x;
            prev_y = start_y;
        }
    });

    // This reacts much faster than the draggable stop event
    $('#joystick-wrapper').bind('touchend mouseup', function() {
        if (moving) {
            stop_motors()
        }
        prev_x = start_x;
        prev_y = start_y;
        return true;
    });

    $('#joystick-wrapper').bind('touchstart mousedown', function() {
        var ajax_url = "/" + seq + "/joystick-engaged/"
        seq++;

        $.ajax({
            type: "GET",
            cache: false,
            dataType: 'text',
            async: true,
            url: ajax_url
        });
    });
});
