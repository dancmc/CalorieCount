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
        form1.append("token", "EAACYVLvmXFkBAIcwRAiV4G2wMXXfHn9cu4yemXm2rbWvHBTV5edwjZCyB1abxMXFiom5iy4fY0HwskKYS6xW0Wu3WMJu9kMVYyCvBZCMHT5exA5MaXOx99h9kFoO4UPeUExRxlXGZB90y5qHhDlZBgagcfZAVByN8GIgJwENheb3NkaXldBc8")
        $.ajax({
            url: '/users/oauthtoken/facebook',
            data: form1,
            type: 'POST',
            contentType: false,
            processData: false,
            success: function (response) {
                localStorage.setItem("access_token", response.token);
                console.log(response)
                var form2 = document.createElement("form")
                document.body.appendChild(form2)
                form2.method = "POST";
                form2.action = "/feed";
                var element1 = document.createElement("input")
                element1.name = "Authorization"
                element1.value = "Bearer "+response.token
                element1.type = "hidden"
                form2.appendChild(element1)

                form2.submit()


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
