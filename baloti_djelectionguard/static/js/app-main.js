var App = {
    currentUrl: window.location.href,

    socialShareUrl: function(elements){
        for(i = 0; i <= arguments.length; i++){
            var hrefPath = $(arguments[i]).attr('href');
            var sharedPath = hrefPath + App.currentUrl;
            $(arguments[i]).attr("href", sharedPath);
        }
    },

    slider : function(sliderClass){
        $(sliderClass).slick({
            dots: true,
            infinite: true,
            speed: 300,
            slidesToShow: 1,
            adaptiveHeight: true,
            arrows: false
        });
    },

    copyToClipboard: function(value, showNotification, notificationText){
        var $temp = $("<input>");
        $("body").append($temp);
        $temp.val(value).select();
        document.execCommand("copy");
        $temp.remove();
    
        if (typeof showNotification === 'undefined') {
            showNotification = true;
        }
        if (typeof notificationText === 'undefined') {
            notificationText = "Copied to clipboard";
        }
    
        var notificationTag = $("div.app-copy-notification");
        if (showNotification && notificationTag.length == 0) {
            notificationTag = $("<div/>", { "class": "app-copy-notification", text: notificationText });
            $("body").append(notificationTag);
    
            notificationTag.fadeIn("slow", function () {
                setTimeout(function () {
                    notificationTag.fadeOut("slow", function () {
                        notificationTag.remove();
                    });
                }, 1000);
            });
        }
    },

    countDownFunc: function(endDAte){
        var second = 1000,
        minute = second * 60,
        hour = minute * 60,
        day = hour * 24;

        var today = new Date(),
        dd = String(today.getDate()).padStart(2, "0"),
        mm = String(today.getMonth() + 1).padStart(2, "0"),
        yyyy = today.getFullYear(),
        nextYear = yyyy + 1,
        dayMonth = endDAte,
        voteday = dayMonth + yyyy;

        today = mm + "/" + dd + "/" + yyyy;
        if (today > voteday) {
        voteday = dayMonth + nextYear;
        }
        //end

        var countDown = new Date(voteday).getTime(),
        x = setInterval(function() {    

        var now = new Date().getTime(),
        distance = countDown - now;

        var daychars = Math.floor(distance / (day));
        var dayArr = Array.from(daychars.toString()).map(Number);
        var dayres = dayArr.map(function(el, i) {
          return `<div class="app-timerlist__num"><span>${el}</span></div>`;
        }).join('');

        var hourschars = Math.floor((distance % (day)) / (hour));
        var hoursArr = Array.from(hourschars.toString()).map(Number);
        var hoursres = hoursArr.map(function(el, i) {
          return `<div class="app-timerlist__num"><span>${el}</span></div>`;
        }).join('');

        var minutechars = Math.floor((distance % (hour)) / (minute));
        var minuteArr = Array.from(minutechars.toString()).map(Number);
        var minuteres = minuteArr.map(function(el, i) {
          return `<div class="app-timerlist__num"><span>${el}</span></div>`;
        }).join('');

        // var secondchars = Math.floor((distance % (minute)) / second);
        // var secondArr = Array.from(secondchars.toString()).map(Number);
        // var secondres = secondArr.map(function(el, i) {
        //   return `<span>${el}</span>`;
        // }).join('');

        document.getElementById("days").innerHTML = dayres,
        document.getElementById("hours").innerHTML = hoursres,
        document.getElementById("minutes").innerHTML = minuteres;
        // document.getElementById("seconds").innerHTML = secondres;

        //do something later when date is reached
        if (distance < 0) {
            document.getElementById("headline").innerText = "Voting Closed!";
            document.getElementById("countdown").style.display = "none";
            clearInterval(x);
        }
        //seconds
        }, 0);
    },

    voteDetailFunc: function(voted, nonVoted){
        var canvas = document.getElementById("electionchart");
        var ctx = canvas.getContext('2d');
        var gradientColors = [
        {
        start: '#CE2323',
        end: '#121567'
        },
        {
        start: '#F3F3F3',
        end: '#C8C8C8'
        }
        ];
        
        var gradients = [];
        
        gradientColors.forEach( function( item ){
            var gradient = ctx.createLinearGradient(0, 0, 0, 150);
            gradient.addColorStop(0, item.start);
            gradient.addColorStop(1, item.end);
            gradients.push(gradient);
        });
        
        
        var doughnutBar = new Chart(canvas, {
        
        type: 'doughnut',
        data: {
            labels: ["A", "B"],
            datasets: [{
                label: "Status",
                backgroundColor: gradients,
                borderColor: 'rgba(73, 79, 92, 0)',
                data: [voted, nonVoted]
            }]
        },
        options: {
            cutout:58,
            plugins: {
              tooltip: {
                enabled: false
              },
              aspectRatio: 1,
            responsive: true,
            startAngle: 0,
              legend: {
                  display: false
              }
          }
        }
        });
    },

    showHideInputPassword : function(iconElement){
        $(iconElement).on('click', function() {
            $(this).toggleClass("icon-view icon-hide");
            var input = $(this).closest(".app-form__control--password").find("input");
            if (input.attr("type") === "password") {
                input.attr("type", "text");
            } else {
                input.attr("type", "password");
            }
    
        });
    },
}


var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
    return new bootstrap.Tooltip(tooltipTriggerEl);
});

// Header Position fixed on scroll
$(window).scroll(function(){
    var sticky = $('.app-header'),
        scroll = $(window).scrollTop();
  
    if (scroll >= 100) sticky.addClass('fixed');
    else sticky.removeClass('fixed');
});