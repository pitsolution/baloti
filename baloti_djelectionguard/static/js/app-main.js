$(window).scroll(function(){
    var sticky = $('.app-header'),
        scroll = $(window).scrollTop();
  
    if (scroll >= 100) sticky.addClass('fixed');
    else sticky.removeClass('fixed');
  });

$(document).ready(function(){
    
    var csrftoken = document.querySelector('[name=csrfmiddlewaretoken]').value;

    $("#showBalletModal").on("click", function(){
        var choice_name = $("input[type='radio']:checked").attr("dataname");
        $('#choice_input').text(choice_name);
        $('#createballet').modal("show");
        var choice = $(".form-check-input:checked").val();

        var href = document.getElementsByClassName("btn btn-facebook btn-block")[0].href;
        var href = href + choice
        $("#fbloginBtn").attr("href", href)

        // var vote_success_url = 'baloti/contest/vote/success/' + choice
        // if(window.location.href.indexOf(vote_success_url) > -1)
        //     {
        //         $('#ballet_success').modal("show");
        //     }
    });


    $("#confirmBtn").on("click", function(){
        $(this).closest(".app-modal").find("#confirmVote").addClass("d-none");
        console.log('ccccccccccccccccccccccccccccccccccccccccc')
        var login = $(this).attr("isloggedIn");
        if($(this).attr("isloggedIn") == "true"){
            var csrftoken = document.querySelector('[name=csrfmiddlewaretoken]').value;
            $(this).closest(".app-modal").find("#appLogin").removeClass("d-none");
            $(this).closest(".app-modal").addClass("app-modal--md");
            $("#success").removeClass("d-none");
            var choice = $(".form-check-input:checked").val();
            $.ajax({
                type: "POST",
                url: '/en/baloti/anonymous/vote/',
                data: {'choice': choice},
                headers: {'X-CSRFToken': csrftoken},
                mode: 'same-origin',
            });
        }
        else{
            $(this).closest(".app-modal").find("#appLogin").removeClass("d-none");
        }
    });


    $("#loginBtn").on("click", function(){
        $(this).closest(".app-modal").find("#appLogin").addClass("d-none");
        var login = $(this).attr("isloggedIn");
        var username = document.getElementById('id_username').value;
        var password = document.getElementById('id_password').value;
        var csrftoken = document.querySelector('[name=csrfmiddlewaretoken]').value;

        var self = this;
        $.ajax({
                type: "POST",
                url: '/en/accounts/login/',
                data: {'username': username, 'password': password, 'csrfmiddlewaretoken': csrftoken},
                headers: {'X-CSRFToken': csrftoken},
                mode: 'same-origin',
                success: function(data){
                        // setTimeout(() => {
                        $(this).closest(".app-modal").find("#success").removeClass("d-none");
                        var choice = $(".form-check-input:checked").val();
                        var vote_url = '/en/baloti/contest/vote/success/' + choice

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
                        $.ajax({
                            headers: {'X-CSRFToken': logincsrftoken},
                            type: "POST",
                            url: '/en/baloti/anonymous/vote/',
                            data: {'choice': choice, 'username': username},
                            credentials: 'include',
                            mode: 'same-origin',
                            success: function(data){
                                $("#login_error").addClass("d-none");
                                $(self).closest(".app-modal").find("#success").removeClass("d-none"); 
                                $(self).closest(".app-modal").find("#appLogin").addClass("d-none");
                            },

                            error:function (xhr, ajaxOptions, thrownError){
                                if(xhr.status==400) {
                                    $("#login_error").removeClass("d-none");
                                    $(self).closest(".app-modal").find("#success").addClass("d-none");
                                    $(self).closest(".app-modal").find("#appLogin").removeClass("d-none");

                                }
                            }
                        });
                    // }, 3000);
                }
            });

    });

    $("#fbloginBtn").on("click", function(){
        $(this).closest(".app-modal").find("#appLogin").addClass("d-none");
    });


    if($("#ballet_success").length > 0){
        $(document).ready(function(){
                $('#ballet_success').modal("show");
            });
    }

    $("#closeBtn").on("click", function(){
        $('#createballet').modal('hide');
    });

    $("#logincloseBtn").on("click", function(){
        $(this).closest(".app-modal").find("#confirmVote").removeClass("d-none");
        $(this).closest(".app-modal").find("#appLogin").addClass("d-none");
        $(this).closest(".app-modal").find("#success").addClass("d-none");
    });

    $("#howitworksbtn").click(function() {
        $('html, body').animate({
            scrollTop: $("#howItWorksSection").offset().top
        }, 2000);
    });

    $("#infomailSubmit").on("click", function(){
        var firstname = document.getElementById('id_firstname').value;
        var lastname = document.getElementById('id_lastname').value;
        var email = document.getElementById('id_email').value;
        var subject = document.getElementById('id_subject').value;
        var message = document.getElementById('id_message').value;
        
        var csrftoken = document.querySelector('[name=csrfmiddlewaretoken]').value;
            $.ajax({
                type: "POST",
                url: '/en/info/submit',
                data: {'firstname': firstname, 'lastname': lastname, 'email': email, 'subject': subject, 'message': message},
                headers: {'X-CSRFToken': csrftoken},
                mode: 'same-origin',
                success: function(data){
                        document.getElementById('id_firstname').value = "";
                        document.getElementById('id_lastname').value = "";
                        document.getElementById('id_email').value = "";
                        document.getElementById('id_subject').value = "";
                        document.getElementById('id_message').value = "";
                        $("#info_mailsent").removeClass("d-none");
                },
                
            });
        
    });

});


