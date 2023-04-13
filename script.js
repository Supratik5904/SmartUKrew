const chatBody = document.getElementById('chat-body');
		const userInput = document.getElementById('user-input');
		const sendButton = document.getElementById('send-button');

		sendButton.addEventListener('click', sendMessage);
		userInput.addEventListener('keydown', function (event) {
		if (event.code === 'Enter') {
			sendMessage();
		}
		});

	function sendMessage() {
		const message = userInput.value;
		const messageElement = document.createElement('p');
		messageElement.innerHTML = '<strong>You:</strong> ' + message;
		chatBody.appendChild(messageElement);
		userInput.value = '';
		const data = new FormData();
        data.append("message", message);
		
		fetch('http://127.0.0.1:5000/chat', {
			method: 'POST',
			body:data
		})
		.then(response => response.json())
		.then(data => {
			const messageElement = document.createElement('p');
			messageElement.innerHTML = '<strong>UKG Assistant:</strong> ' + data.message;
			chatBody.appendChild(messageElement);
		})
    .catch(error => console.error(error));
}