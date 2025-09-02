document.addEventListener('DOMContentLoaded', () => {
    const fileInput = document.getElementById('fileInput');
    const uploadButton = document.getElementById('uploadButton');
    const uploadStatus = document.getElementById('uploadStatus');

    const reIngestButton = document.getElementById('reIngestButton');
    const reIngestStatus = document.getElementById('reIngestStatus');

    const userInput = document.getElementById('userInput');
    const sendButton = document.getElementById('sendButton');
    const chatbox = document.getElementById('chatbox');

    // File Upload
    if (uploadButton) {
        uploadButton.addEventListener('click', async () => {
            const file = fileInput.files[0];
            if (!file) {
                uploadStatus.textContent = 'Please select a file first.';
                uploadStatus.className = 'status-message error';
                return;
            }

            const formData = new FormData();
            formData.append('file', file);

            uploadStatus.textContent = 'Uploading and ingesting... Please wait.';
            uploadStatus.className = 'status-message';
            uploadButton.disabled = true;

            try {
                const response = await fetch('/file_upload', {
                    method: 'POST',
                    body: formData
                });
                const result = await response.json();

                if (response.ok) {
                    uploadStatus.textContent = result.message || 'File processed successfully!';
                    uploadStatus.className = 'status-message success';
                } else {
                    uploadStatus.textContent = `Error: ${result.error || 'Unknown error during upload/ingestion.'}`;
                    uploadStatus.className = 'status-message error';
                }
            } catch (error) {
                uploadStatus.textContent = `Network error: ${error.message}`;
                uploadStatus.className = 'status-message error';
            }
            fileInput.value = ''; // Clear the file input
            uploadButton.disabled = false;
        });
    }

    // Re-Ingest All
    if (reIngestButton) {
        reIngestButton.addEventListener('click', async () => {
            reIngestStatus.textContent = 'Ingesting all documents... Please wait.';
            reIngestStatus.className = 'status-message';
            reIngestButton.disabled = true;

            try {
                const response = await fetch('/ingest', {
                    method: 'POST'
                });
                const result = await response.json();
                if (response.ok) {
                    reIngestStatus.textContent = result.message || 'Ingestion complete!';
                    reIngestStatus.className = 'status-message success';
                } else {
                    reIngestStatus.textContent = `Error: ${result.error || 'Ingestion failed'}`;
                    reIngestStatus.className = 'status-message error';
                }
            } catch (error) {
                reIngestStatus.textContent = `Network error: ${error.message}`;
                reIngestStatus.className = 'status-message error';
            }
            reIngestButton.disabled = false;
        });
    }


    // Chat
    if (sendButton) {
        sendButton.addEventListener('click', handleSendMessage);
    }
    if (userInput) {
        userInput.addEventListener('keypress', (event) => {
            if (event.key === 'Enter') {
                handleSendMessage();
            }
        });
    }

    async function handleSendMessage() {
        const query = userInput.value.trim();
        if (!query) return;

        addMessageToChatbox('User', query);
        userInput.value = ''; // Clear input field

        // Add a temporary "thinking" message for the bot
        const thinkingMsgId = `bot-thinking-${Date.now()}`;
        addMessageToChatbox('Bot', 'Thinking...', null, thinkingMsgId);
        sendButton.disabled = true;
        userInput.disabled = true;

        try {
            const response = await fetch('/chat', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ query: query })
            });

            removeMessageById(thinkingMsgId); // Remove "Thinking..." message
            const result = await response.json();

            if (response.ok && result.answer) {
                addMessageToChatbox('Bot', result.answer.answer, result.answer.sources);
            } else {
                addMessageToChatbox('Bot', result.error || 'Sorry, I encountered an error.');
            }
        } catch (error) {
            removeMessageById(thinkingMsgId); // Remove "Thinking..." message
            addMessageToChatbox('Bot', `Network error: ${error.message}`);
        }
        sendButton.disabled = false;
        userInput.disabled = false;
        userInput.focus();
    }

    function addMessageToChatbox(sender, text, sources = null, messageId = null) {
        const messageDiv = document.createElement('div');
        messageDiv.classList.add('message');
        if (messageId) {
            messageDiv.id = messageId;
        }

        if (sender === 'User') {
            messageDiv.classList.add('user-message');
            messageDiv.textContent = text;
        } else {
            messageDiv.classList.add('bot-message');

            const textParagraph = document.createElement('p');
            textParagraph.textContent = text;
            messageDiv.appendChild(textParagraph);

            if (sources && sources.length > 0) {
                const sourcesDiv = document.createElement('div');
                sourcesDiv.classList.add('sources');
                let sourcesHtml = '<strong>Sources:</strong><ul>';
                sources.forEach(s => {
                    // Sanitize source string to prevent XSS if sources can be arbitrary strings
                    const cleanSource = s ? String(s).replace(/</g, "<").replace(/>/g, ">") : 'N/A';
                    sourcesHtml += `<li>${cleanSource}</li>`;
                });
                sourcesHtml += '</ul>';
                sourcesDiv.innerHTML = sourcesHtml;
                messageDiv.appendChild(sourcesDiv);
            }
        }
        chatbox.appendChild(messageDiv);
        chatbox.scrollTop = chatbox.scrollHeight; // Scroll to bottom
    }

    function removeMessageById(messageId) {
        const messageElement = document.getElementById(messageId);
        if (messageElement) {
            messageElement.remove();
        }
    }
});
