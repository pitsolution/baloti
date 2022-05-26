$(document).ready(function(){
var myJson = {}
get_something()
function get_something(){
    $.getJSON("/static/translations.json", function(json){
        myJson = json;
        console.log(myJson,'jgdgrsfjh')

    });
}

    var language = localStorage.getItem('languageObject').replaceAll('"', '');
    console.log(myJson,'jsonnnnnnn')
    $(".copytoclipboard").click(function (event) {
        event.preventDefault();
        App.copyToClipboard(App.currentUrl, true, "URL copied");
    });

    $("#deleteProfileStep2").on("click", function(){
        $(this).closest('.modal-confirmbox').addClass("d-none");
        $(this).closest('.modal-body').find('.modal-confirmbox--step-2').removeClass("d-none");
    });

    $("#deleteProfileConfirm").on("click", function(){
        var password = document.getElementById('idPassword').value;
        var username = document.getElementById('idusername').value;
        function getCookie(name) {
                let cookieValue = null;
                if (document.cookie && document.cookie !== '') {
                    const cookies = document.cookie.split(';');
                    for (let i = 0; i < cookies.length; i++) {
                        const cookie = cookies[i].trim();
                        // Does this cookie string begin with the name we want?
                        if (cookie.substring(0, name.length + 1) === (name + '=')) {
                            cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                            break;
                        }
                    }
                }
                return cookieValue;
            }
        const csrftoken = getCookie('csrftoken');

        $.ajax({
            type: "POST",
            url: '/' + language + '/baloti/delete/profile',
            data: {'password': password, 'username': username},
            headers: {'X-CSRFToken': csrftoken},
            mode: 'same-origin',
            success: function(data){
                if(data=='invalid_password') {
                    $("#userpassword_error").removeClass("d-none");
                }
                else {
                    $('#deleteProfile').modal('hide');
                    window.location.reload();
                }
            }
        });
    });

    App.showHideInputPassword('.show-hide-password');
    
    $("#filter").keyup(function() {
        var filter = $(this).val(),
        count = 0;
        var cardlength = $('.app-elections__vote .search').length;
        $('.search').each(function() {
            if ($(this).text().search(new RegExp(filter, "i")) < 0) {
                $(this).addClass('d-none');
                $(this).closest('.app-elections__result').addClass('d-none');
            } 
            else {
                $(this).removeClass('d-none');
                $(this).closest('.app-elections__result').removeClass('d-none');
                count++;
            }
        });
        displayNoResult(cardlength, '.app-elections__vote .search');
    });

    $(".app-newslist__searchinput").on("click", function(){
        $('.app-newslist__searchbox input').val("");
        $('#filter').trigger("keyup");
    });

    function displayNoResult(cardCount, card) {
        var hiddenLILength = $(card).parent().find('.d-none');
        if (cardCount === hiddenLILength.length || card.length === 0) {
          $('.app-nodata').show();
          $('.app-nodata').parent().addClass('app-griditem--nodata');
          $(hiddenLILength).closest('.app-elections__result').addClass('d-none');
        } else {
            $('.app-nodata').hide();
            $('.app-nodata').parent().removeClass('app-griditem--nodata');
            $(hiddenLILength).closest('.app-elections__result').removeClass('d-none');
        }
    }
    displayNoResult($(".app-elections__vote .search").length, '.search');
    if($('.app-elections__result .search').length === 0){
        $('.app-elections__result').addClass('d-none');
    }
    
    $("#showBalletModal").on("click", function(){
        var choice_name = $("input[type='radio']:checked").attr("dataname");
        $('#choice_input').text(choice_name);
        $('#createballet').modal("show");
        var choice = $(".form-check-input:checked").val();

        var href = document.getElementsByClassName("btn btn-facebook btn-block")[0].href;
        var href = href + '/'+ language + '/baloti/contest/vote/success/' + choice
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
                url: '/'+ language + '/baloti/anonymous/vote/',
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
                url: '/'+ language + '/baloti/login/',
                data: {'username': username, 'password': password, 'csrfmiddlewaretoken': csrftoken},
                headers: {'X-CSRFToken': csrftoken},
                mode: 'same-origin',
                success: function(data){
                        // setTimeout(() => {
                        $(this).closest(".app-modal").find("#success").removeClass("d-none");
                        var choice = $(".form-check-input:checked").val();
                        var vote_url = '/'+ language + '/baloti/contest/vote/success/' + choice

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
                            url: '/'+ language + '/baloti/anonymous/vote/',
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
        $(this).closest("#appLogin").addClass("d-none");
        $("#idSignup").removeClass("d-none");

    });
    $("#idButtonLogin").on("click", function(){
        $(this).closest("#idSignup").addClass("d-none");
        $("#appLogin").removeClass("d-none");

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
                url: '/'+ language + '/baloti/modalsignup/mailsent/',
                data: {'email': email, 'csrfmiddlewaretoken': csrftoken},
                headers: {'X-CSRFToken': csrftoken},
                dataType: "text",
                mode: 'same-origin',
                success: function(data, textStatus, jqXHR){
                    $("#appLogin").addClass("d-none");
                    $("#idSignup").addClass("d-none");
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
            console.log(myJson,'hgghjghghjg')
            // alert('ddsdsd errorrnknnlk')
            $("#info_mailsent").removeClass("d-none");
            var trans_text = $("html").attr("lang")
            $("#message_text").text(myJson['text_b'][0][trans_text]);


            $("#info_mailsent").addClass("error");
            $(".app-toast__tick").addClass("d-none");
        }
        else if(!pattern.test(email)){
            $("#info_mailsent").removeClass("d-none");
            var trans_text = $("html").attr("lang")
            $("#message_text").text(myJson['text_d'][0][trans_text]);

            $("#info_mailsent").addClass("error");
            $(".app-toast__tick").addClass("d-none");
        }
        else{
            $.ajax({
                type: "POST",
                url: '/'+ language + '/info/submit',
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
                        var trans_text = $("html").attr("lang")
                          $("#message_text").text(myJson['text_a'][0][trans_text]);




                        $("#info_mailsent").removeClass("d-none");
                        $("#info_mailsent").removeClass("error");
                        $(".app-toast__tick").removeClass("d-none");
                },
                error:function (xhr, ajaxOptions, thrownError){
                    if(xhr.status==400) {
                        var trans_text = $("html").attr("lang")
                        $("#message_text").text(myJson['text_c'][0][trans_text]);

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

    if($(window).width() < 768){
        App.slider("#illustrationSlider");
    }
});
