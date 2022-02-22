$(window).scroll(function(){
    var sticky = $('.app-header'),
        scroll = $(window).scrollTop();
  
    if (scroll >= 100) sticky.addClass('fixed');
    else sticky.removeClass('fixed');
  });

function updateShareUrl(elements){

    var currentLocation = window.location.href;

    for(i = 0; i <= arguments.length; i++){
        var hrefPath = $(arguments[i]).attr('href');
        var sharedPath = hrefPath + currentLocation;
        $(arguments[i]).attr("href", sharedPath);
    }
}

$(document).ready(function(){

    updateShareUrl(".share-facebook", ".share-twitter", ".share-whatsapp", ".share-email", ".share-linkedin");

    $(".copytoclipboard").click(function (event) {
        event.preventDefault();
        CopyToClipboard(window.location.href, true, "URL copied");
    });

    $("#deleteProfileStep2").on("click", function(){
        $(this).closest('.modal-confirmbox').addClass("d-none");
        $(this).closest('.modal-body').find('.modal-confirmbox--step-2').removeClass("d-none");
    });
    $('#showHidePassword').on('click', function() {
        $(this).toggleClass("icon-view icon-hide");
        var input = $(this).closest(".app-form__control--password").find("input");
        if (input.attr("type") === "password") {
            input.attr("type", "text");
        } else {
            input.attr("type", "password");
        }

    });
    $("#filter").keyup(function() {
        var filter = $(this).val(),
        count = 0;

        $('.search').each(function() {
            if ($(this).text().search(new RegExp(filter, "i")) < 0) {
                $(this).hide();
            } else {
                $(this).show();
                count++;
            }
        });
    });

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
        var login = $(this).attr("isloggedIn");
        if($(this).attr("isloggedIn") == "true"){
            var csrftoken = document.querySelector('[name=csrfmiddlewaretoken]').value;
            $(this).closest(".app-modal").find("#appLogin").removeClass("d-none");
            $(this).closest(".app-modal").addClass("app-modal--md app-modal--success");
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
                            success: function(data, textStatus, jqXHR){
                                if(data=='voted') {
                                    $("#login_error").addClass("d-none");
                                    $(self).closest(".app-modal").find("#alreadyVoted").removeClass("d-none");
                                    $(self).closest(".app-modal").find("#appLogin").addClass("d-none");
                                }
                                else {
                                    $("#login_error").addClass("d-none");
                                    $(self).closest(".app-modal").find("#success").removeClass("d-none"); 
                                    $(self).closest(".app-modal").find("#appLogin").addClass("d-none");
                                }
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

    $("#idCreateAccount").on("click", function(){
        $(this).closest(".app-form").addClass("d-none");
        $("#idSignup").closest(".app-form").removeClass("d-none");

    });
    $("#idButtonLogin").on("click", function(){
        $(this).closest(".app-form").addClass("d-none");
        $("#idLogin").closest(".app-form").removeClass("d-none");

    });

    $("#idButtonLoginAfterSuccess").on("click", function(){
        $("#appLogin").removeClass("d-none");
        $("#idsignupSuccess").addClass("d-none");

        $("#idLogin").removeClass("d-none");
        $("#idSignup").addClass("d-none");

    });

    $("#signupBtn").on("click", function(){
        var email = document.getElementById('exampleInputEmail1').value;
        var pattern = new RegExp(/^[+a-zA-Z0-9._-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,4}$/i);
        if(!email || !pattern.test(email)){
            $("#signup_error").addClass("d-none");
            $("#signup_nofielderror").removeClass("d-none");
        }
        else{


        var self = this;
        var csrftoken = document.querySelector('[name=csrfmiddlewaretoken]').value;

        $.ajax({
                type: "POST",
                url: '/en/baloti/modalsignup/mailsent/',
                data: {'email': email, 'csrfmiddlewaretoken': csrftoken},
                headers: {'X-CSRFToken': csrftoken},
                dataType: "text",
                mode: 'same-origin',
                success: function(data, textStatus, jqXHR){
                    $("#appLogin").addClass("d-none");
                    $("#idsignupSuccess").removeClass("d-none");
                    $("#signup_error").addClass("d-none");
                    $("#signup_nofielderror").addClass("d-none");
                },

                error:function (xhr, ajaxOptions, thrownError){
                    $("#signup_error").removeClass("d-none");
                    $("#signup_nofielderror").addClass("d-none");
                }
            });
        }

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

    $("#closeMailSent").click(function() {
        $(this).closest(".app-toast").addClass("d-none");
    });

    $("#infomailSubmit").on("click", function(){
        var pattern = new RegExp(/^[+a-zA-Z0-9._-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,4}$/i);
        var firstname = document.getElementById('id_firstname').value;
        var lastname = document.getElementById('id_lastname').value;
        var email = document.getElementById('id_email').value;
        var subject = document.getElementById('id_subject').value;
        var message = document.getElementById('id_message').value;
        
        var csrftoken = document.querySelector('[name=csrfmiddlewaretoken]').value;
        // if (!$("#info_mailsent").hasClass("d-none") ) {
        //     $("#info_mailsent").addClass("d-none");
        // }
        if(!firstname || !lastname || !email || !subject || !message){
            console.log('hgghjghghjg')
            // alert('ddsdsd errorrnknnlk')
            $("#info_mailsent").removeClass("d-none");
            if($("html").attr("lang") == "de" ){
            $("#message_text").text(' Füllen Sie alle Felder aus');}
            else
            {
            $("#message_text").text('Fill all the fields');
            }

            $("#info_mailsent").addClass("error");
            $(".app-toast__tick").addClass("d-none");
        }
        else if(!pattern.test(email)){
            $("#info_mailsent").removeClass("d-none");
            if($("html").attr("lang") == "de" ){
            $("#message_text").text('Ungültige E-Mail');}
            else
            {
            $("#message_text").text('Invalid Email Address');
            }
            $("#info_mailsent").addClass("error");
            $(".app-toast__tick").addClass("d-none");
        }
        else{
            $.ajax({
                type: "POST",
                url: '/en/info/submit',
                data: {'firstname': firstname, 'lastname': lastname, 'email': email, 'subject': subject, 'message': message},
                headers: {'X-CSRFToken': csrftoken},
                mode: 'same-origin',
                beforeSend: function(){
                                $('body').append('<div class="app-loaderwrap"><div class="app-loader"></div></div>');
                            },
                            complete: function(){
                                $('.app-loaderwrap').remove();                       
                            },
                success: function(data){
                        document.getElementById('id_firstname').value = "";
                        document.getElementById('id_lastname').value = "";
                        document.getElementById('id_email').value = "";
                        document.getElementById('id_subject').value = "";
                        document.getElementById('id_message').value = "";
                        if($("html").attr("lang") == "de" ){
                          $("#message_text").text('E-Mail erfolgreich versendet');
                        }
                        else {
                         $("#message_text").text('Mail sent successfully');
                        }

                        $("#info_mailsent").removeClass("d-none");
                        $("#info_mailsent").removeClass("error");
                        $(".app-toast__tick").removeClass("d-none");
                },
                error:function (xhr, ajaxOptions, thrownError){
                    if(xhr.status==400) {
                        if($("html").attr("lang") == "de" ){
                        $("#message_text").text('Dienst nicht verfügbar');}
                        else
                        {
                        $("#message_text").text('Service not available');
                        }
                        $("#info_mailsent").removeClass("d-none")
                        $("#info_mailsent").addClass("error");
                        $(".app-toast__tick").addClass("d-none");
                    }
                }
                
            });
        }
        
    });


    $("#howitworksbtn").click(function() {
        $('html, body').animate({
            scrollTop: $("#howItWorksSection").offset().top
        }, 2000);
    });
    $(".app-showmore").on("click", function(){
        $(this).hide();
    });
    if($(window).width() < 768){
        App.slider("#illustrationSlider");
    }
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'))
    var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
    return new bootstrap.Tooltip(tooltipTriggerEl)
    });
});

function CopyToClipboard(value, showNotification, notificationText) {
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
}

var App = {
    slider : function(sliderClass){
        $(sliderClass).slick({
            dots: true,
            infinite: true,
            speed: 300,
            slidesToShow: 1,
            adaptiveHeight: true,
            arrows: false
        });
    }
}

