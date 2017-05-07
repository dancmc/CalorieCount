$(function(){
	$('#btnSignUp').click(function(){
		
		$.ajax({
			url: '/users/new/standard',
			data: $('form').serialize(),
			type: 'POST',
			success: function(response){
window.location.replace(response)
			console.log(response)
			},
			error: function(error){
				console.log(error);
			}
		});
	});
});