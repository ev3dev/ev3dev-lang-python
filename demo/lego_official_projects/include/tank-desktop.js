
var moving = 0;
var ip = 0;
var seq = 0;

function stop_motors() {
    var ajax_url = "/" + seq + "/move-stop/"
    seq++;

    $.ajax({
        type: "GET",
        cache: false,
        dataType: 'text',
        url: ajax_url
    });

    moving = 0
}

function stop_medium_motor() {
    var ajax_url = "/" + seq + "/motor-stop/medium/"
    seq++;

    $.ajax({
        type: "GET",
        cache: false,
        dataType: 'text',
        url: ajax_url
    });
    return false;
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

    $("#medium-motor-speed").slider({
        min: 0,
        max: 100,
        step: 5,
        value: 50
    });

    $("#tank-speed").slider({
        min: 0,
        max: 100,
        step: 5,
        value: 25
    });

    // Desktop Interface
    $('#ArrowUp').bind('touchstart mousedown', function() {
        console.log('ArrowUp down')
        var power = $('#tank-speed').slider("value")
        var ajax_url = "/" + seq + "/move-start/forward/" + power + "/"
        seq++;
        moving = 1

        $.ajax({
            type: "GET",
            cache: false,
            dataType: 'text',
            url: ajax_url
        });
        return false;
    });

    $('#ArrowDown').bind('touchstart mousedown', function() {
        console.log('ArrowDown down')
        var power = $('#tank-speed').slider("value")
        var ajax_url = "/" + seq + "/move-start/backward/" + power + "/"
        seq++;
        moving = 1

        $.ajax({
            type: "GET",
            cache: false,
            dataType: 'text',
            url: ajax_url
        });
        return false;
    });

    $('#ArrowLeft').bind('touchstart mousedown', function() {
        console.log('ArrowLeft down')
        var power = $('#tank-speed').slider("value")
        var ajax_url = "/" + seq + "/move-start/left/" + power + "/"
        seq++;
        moving = 1

        $.ajax({
            type: "GET",
            cache: false,
            dataType: 'text',
            url: ajax_url
        });
        return false;
    });

    $('#ArrowRight').bind('touchstart mousedown', function() {
        console.log('ArrowRight down')
        var power = $('#tank-speed').slider("value")
        var ajax_url = "/" + seq + "/move-start/right/" + power + "/"
        seq++;
        moving = 1

        $.ajax({
            type: "GET",
            cache: false,
            dataType: 'text',
            url: ajax_url
        });
        return false;
    });

    $('#desktop-medium-motor-spin .CounterClockwise').bind('touchstart mousedown', function() {
        console.log('CounterClockwise down')
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

    $('#desktop-medium-motor-spin .Clockwise').bind('touchstart mousedown', function() {
        console.log('Clockwise down')
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

    $('.medium').bind('touchend mouseup mouseout', function() {
        stop_medium_motor()
        return false;
    });

    $('.nav').bind('touchend mouseup mouseout', function() {
        if (moving) {
            console.log('Mouse no longer over button')
            stop_motors()
            return false;
        }
    });
});
