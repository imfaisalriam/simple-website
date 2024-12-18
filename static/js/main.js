// JavaScript for handling live chat with Socket.IO
var socket = io.connect(window.location.origin);

function sendMessage() {
    var message = document.getElementById('chat-message').value;
    if (message) {
        socket.send(message);
        document.getElementById('chat-message').value = '';  // Clear the input field
    }
}

// Listen for incoming messages and append them to the chat
socket.on('message', function(data) {
    var chatBox = document.getElementById('chat-box');
    var message = document.createElement('div');
    message.classList.add('chat-message');
    message.innerHTML = `<strong>${data.username}:</strong> ${data.message} <em>(${data.time})</em>`;
    chatBox.appendChild(message);
    chatBox.scrollTop = chatBox.scrollHeight;  // Auto-scroll to the latest message
});
