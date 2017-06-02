jQuery(document).ready(function () {

    /*
     Fullscreen background
     */
    $.backstretch("../static/img/backgrounds/1.jpg");

    /*
     Login form validation
     */
    $('.login-form input[type="text"], .login-form input[type="password"], .login-form textarea').on('focus', function () {
        $(this).removeClass('input-error');
    });

    $('.login-form').on('submit', function (e) {

        $(this).find('input[type="text"], input[type="password"], textarea').each(function () {
            if ($(this).val() == "") {
                e.preventDefault();
                $(this).addClass('input-error');
            }
            else {
                $(this).removeClass('input-error');
            }
        });

    });

    $('#facebook_button').click(function () {
        var form1 = new FormData();
        // TODO get token from fb
        form1.append("token", "EAACYVLvmXFkBAFZCYO7WF2SbBZCtmfd8Vdgpw5Ychx9iqTN4IPOpBjcLFffCZAvfH5hX9YyQTsPpm4NEZAwaDi0v8XZApsJgSICoHT9sfPXKbRUVpr6e533NIGJSSLwW3glurTOHaqe08NIG3CZCNpXTBHFrGnzEJBPLGYMITZC80hu0t0iIIDA")
        $.ajax({
            url: '/users/oauthtoken/facebook',
            data: form1,
            type: 'POST',
            contentType: false,
            processData: false,
            success: function (response) {
                if(response.success) {
                    localStorage.setItem("token", response.token);
                    console.log(response)
                    var form2 = document.createElement("form")
                    document.body.appendChild(form2)
                    form2.method = "POST";
                    form2.action = "/feed";
                    var element1 = document.createElement("input")
                    element1.name = "X-CSRF-TOKEN"
                    element1.value = "Bearer " + response.token
                    element1.type = "hidden"
                    form2.appendChild(element1)

                    form2.submit()
                } else {
                    alert(response.error)
                    console.log(response.error)
                }


                // window.location = "/feed"
            },
            error: function (error) {
                console.log(error);
            }
        });
    });


    /*
     Registration form validation
     */
    $('.registration-form input[type="text"], .registration-form textarea').on('focus', function () {
        $(this).removeClass('input-error');
    });

    $('.registration-form').on('submit', function (e) {

        $(this).find('input[type="text"], textarea').each(function () {
            if ($(this).val() == "") {
                e.preventDefault();
                $(this).addClass('input-error');
            }
            else {
                $(this).removeClass('input-error');
            }
        });

    });


});
