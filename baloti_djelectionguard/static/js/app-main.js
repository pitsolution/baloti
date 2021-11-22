$(window).scroll(function(){
    var sticky = $('.app-header'),
        scroll = $(window).scrollTop();
  
    if (scroll >= 100) sticky.addClass('fixed');
    else sticky.removeClass('fixed');
  });

$(document).ready(function(){
    const csrftoken = document.querySelector('[name=csrfmiddlewaretoken]').value;
    $("#showBalletModal").on("click", function(){
        $('#createballet').modal("show");
    });


    $("#confirmBtn").on("click", function(){
        $(this).closest(".app-modal").find("#confirmVote").addClass("d-none");
        var login = $(this).attr("isloggedIn");
        if($(this).attr("isloggedIn") == "true"){
            $(this).closest(".app-modal").addClass("app-modal--md");
            $(this).closest(".app-modal").find("#appLogin").removeClass("d-none");
            $("#success").removeClass("d-none");
            var choice = $(".form-check-input:checked").val();
            $.ajax({
                type: "POST",
                url: '/en/baloti/anonymous/vote/',
                data: {'choice': choice},
                headers: {'X-CSRFToken': csrftoken},
                mode: 'same-origin',
                success: function(data){
                     alert(data);         
                    }
            });
        }
        else{
            $(this).closest(".app-modal").find("#appLogin").removeClass("d-none");
        }
    });



    $("#closeBtn").on("click", function(){
        console.log('hhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhh')
        $('#createballet').modal('hide');
    });

    // $('#closemodal').click(function() {
    //     $('#modalwindow').modal('hide');
    // });




    $("#loginBtn").on("click", function(){
        $(this).closest(".app-modal").find("#appLogin").addClass("d-none");
        var login = $(this).attr("isloggedIn");
        var username = document.getElementById('id_username').value;
        var password = document.getElementById('id_password').value;
      
        $.ajax({
                type: "POST",
                url: '/en/accounts/login/',
                data: {'username': username, 'password': password, 'csrfmiddlewaretoken': csrftoken},
                headers: {'X-CSRFToken': csrftoken},
                mode: 'same-origin',
            });

        function getCookie(name) {
            var cookieValue = null;
            if (document.cookie && document.cookie !== '') {
                var cookies = document.cookie.split(';');
                for (var i = 0; i < cookies.length; i++) {
                    var cookie = jQuery.trim(cookies[i]);
                    if (cookie.substring(0, name.length + 1) === (name + '=')) {
                        cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                        break;
                    }
                }
            }
            return cookieValue;
        }
        var logincsrftoken = getCookie('csrftoken');
        $(this).closest(".app-modal").find("#success").removeClass("d-none");
        var choice = $(".form-check-input:checked").val();
        
        $.ajax({
            type: "POST",
            url: '/en/baloti/anonymous/vote/',
            data: {'choice': choice, 'username': username },
            credentials: 'include',
            headers: {'X-CSRFToken': logincsrftoken},
            mode: 'same-origin',
        });
        // $.ajax({
        //     "method":'POST',
        //     "url": '/en/baloti/anonymous/vote/',
        //     "data": {'choice': choice, 'username': username },
        //     "credentials": 'include',
        //     "headers":{
        //         "X-CSRFToken": logincsrftoken,
        //         "Accept": "application/json",
        //         "Content-Type": "application/json",
        //     }
        // });
    });

});


