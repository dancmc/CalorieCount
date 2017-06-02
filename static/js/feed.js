$(document).ready(function () {
    function findGetParameter(parameterName) {
        var result = null,
            tmp = [];
        location.search
            .substr(1)
            .split("&")
            .forEach(function (item) {
                tmp = item.split("=");
                if (tmp[0] === parameterName) result = decodeURIComponent(tmp[1]);
            });
        return result;
    }

    function parseJwt(token) {
        var base64Url = token.split('.')[1];
        var base64 = base64Url.replace('-', '+').replace('_', '/');
        return JSON.parse(window.atob(base64));
    }

    token = localStorage.getItem("token");

    json = parseJwt(token)
    id = json.user_id
    console.log(id)

    $.ajax({
        url: "/clients/" + id + "/calories/entries",
        type: 'GET',
        beforeSend: function (xhr) {
            xhr.setRequestHeader('X-CSRF-TOKEN', 'Bearer ' + token);
        },
        async: true,
        cache: false,
        contentType: false,
        processData: false,
        xhrFields: {
            withCredentials: true
        },
        // enctype:"base64",
        success: function (returndata) {
            console.log(returndata)
            arr = returndata.results
            console.log(arr)
            arr.forEach(function (item) {
                console.log(item.image_url)
            })
            console.log(arr[0].image_url)
            $("#img1").attr("src", arr[0].image_url)
            var div1 = $("#div1");
            $('<p />').text('Time in ms : ' + json.timestamp).appendTo(div1)
            $('<p />').text('Your comment : ' + json.client_comment).appendTo(div1)
            $('<p />').text("Trainer's comment : " + json.trainer_comment).appendTo(div1)
            $('<p />').text('Calories : ' + json.calories).appendTo(div1)
            $('<p />').text('Carb : ' + json.carb).appendTo(div1)
            $('<p />').text('Protein : ' + json.protein).appendTo(div1)
            $('<p />').text('Fat : ' + json.fat).appendTo(div1)

            $("#img2").attr("src", arr[1].image_url)
            var div2 = $("#div2");
            $('<p />').text('Time in ms : ' + json.timestamp).appendTo(div2)
            $('<p />').text('Your comment : ' + json.client_comment).appendTo(div2)
            $('<p />').text("Trainer's comment : " + json.trainer_comment).appendTo(div2)
            $('<p />').text('Calories : ' + json.calories).appendTo(div2)
            $('<p />').text('Carb : ' + json.carb).appendTo(div2)
            $('<p />').text('Protein : ' + json.protein).appendTo(div2)
            $('<p />').text('Fat : ' + json.fat).appendTo(div2)

            $("#img3").attr("src", arr[2].image_url)
            var div3 = $("#div3");
            $('<p />').text('Time in ms : ' + json.timestamp).appendTo(div3)
            $('<p />').text('Your comment : ' + json.client_comment).appendTo(div3)
            $('<p />').text("Trainer's comment : " + json.trainer_comment).appendTo(div3)
            $('<p />').text('Calories : ' + json.calories).appendTo(div3)
            $('<p />').text('Carb : ' + json.carb).appendTo(div3)
            $('<p />').text('Protein : ' + json.protein).appendTo(div3)
            $('<p />').text('Fat : ' + json.fat).appendTo(div3)

            $("#img4").attr("src", arr[3].image_url)
            var div4 = $("#div4");
            $('<p />').text('Time in ms : ' + json.timestamp).appendTo(div4)
            $('<p />').text('Your comment : ' + json.client_comment).appendTo(div4)
            $('<p />').text("Trainer's comment : " + json.trainer_comment).appendTo(div4)
            $('<p />').text('Calories : ' + json.calories).appendTo(div4)
            $('<p />').text('Carb : ' + json.carb).appendTo(div4)
            $('<p />').text('Protein : ' + json.protein).appendTo(div4)
            $('<p />').text('Fat : ' + json.fat).appendTo(div4)

            $("#img5").attr("src", arr[4].image_url)
            var div5 = $("#div5");
            $('<p />').text('Time in ms : ' + json.timestamp).appendTo(div5)
            $('<p />').text('Your comment : ' + json.client_comment).appendTo(div5)
            $('<p />').text("Trainer's comment : " + json.trainer_comment).appendTo(div5)
            $('<p />').text('Calories : ' + json.calories).appendTo(div5)
            $('<p />').text('Carb : ' + json.carb).appendTo(div5)
            $('<p />').text('Protein : ' + json.protein).appendTo(div5)
            $('<p />').text('Fat : ' + json.fat).appendTo(div5)

        },
        error: function(error){
            alert(error.error)
        }
    })

});