// SINEMA Chatbot - Enhanced Frontend JavaScript
document.addEventListener('DOMContentLoaded', function () {
    // Elements
    const messageInput = document.getElementById('messageInput');
    const sendBtn = document.getElementById('sendBtn');
    const chatMessages = document.getElementById('chatMessages');
    const typingIndicator = document.getElementById('typingIndicator');
    const refreshBtn = document.getElementById('refreshBtn');
    const newChatBtn = document.getElementById('newChatBtn');
    const uploadBtn = document.getElementById('uploadBtn');
    const uploadModal = document.getElementById('uploadModal');
    const closeUploadModal = document.getElementById('closeUploadModal');
    const uploadZone = document.getElementById('uploadZone');
    const fileInput = document.getElementById('fileInput');
    const selectFileBtn = document.getElementById('selectFileBtn');
    const uploadStatus = document.getElementById('uploadStatus');
    const sessionInfo = document.getElementById('sessionInfo');

    // Session management
    let sessionId = localStorage.getItem('chatSessionId') || null;
    let messageIndex = 0;

    // Initialize session
    async function initSession() {
        if (!sessionId) {
            const res = await fetch('/api/session/new', { method: 'POST' });
            const data = await res.json();
            sessionId = data.session_id;
            localStorage.setItem('chatSessionId', sessionId);
        }
        sessionInfo.textContent = `Session: ${sessionId.substring(0, 8)}...`;
        loadHistory();
    }

    // Load chat history
    async function loadHistory() {
        try {
            const res = await fetch(`/api/session/${sessionId}/history`);
            const data = await res.json();

            if (data.messages && data.messages.length > 0) {
                // Clear welcome message if there's history
                const welcomeMsg = chatMessages.querySelector('.bot-message');
                if (welcomeMsg && data.messages.length > 0) {
                    // Keep welcome message, add history after
                }

                data.messages.forEach((msg, idx) => {
                    addMessage(msg.content, msg.role === 'user' ? 'user' : 'bot', msg.sources, msg.latency, false);
                    messageIndex = idx + 1;
                });
                scrollToBottom();
            }
        } catch (error) {
            console.log('No history loaded');
        }
    }

    // Send message
    async function sendMessage() {
        const message = messageInput.value.trim();
        if (!message) return;

        // Add user message to chat
        addMessage(message, 'user');
        messageInput.value = '';
        messageInput.focus();

        // Show typing indicator
        showTyping(true);
        scrollToBottom();

        try {
            const response = await fetch('/api/chat', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ message: message, session_id: sessionId })
            });

            const data = await response.json();

            if (data.error) {
                addMessage('Maaf, terjadi kesalahan: ' + data.error, 'bot', null, null);
            } else {
                addMessage(data.response, 'bot', data.sources, data.latency, true, data.cached);
                messageIndex++;
            }
        } catch (error) {
            addMessage('Maaf, tidak dapat terhubung ke server.', 'bot', null, null);
        }

        showTyping(false);
        scrollToBottom();
    }

    // Add message to chat with Markdown support
    function addMessage(content, type, sources = null, latency = null, enableFeedback = false, cached = false) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${type}-message`;
        messageDiv.dataset.index = messageIndex;

        const avatar = document.createElement('div');
        avatar.className = 'message-avatar';
        avatar.textContent = type === 'user' ? '👤' : '🤖';

        const contentDiv = document.createElement('div');
        contentDiv.className = 'message-content';

        // Render Markdown for bot messages
        if (type === 'bot' && typeof marked !== 'undefined') {
            contentDiv.innerHTML = marked.parse(content);
        } else {
            // Format content with paragraphs
            const paragraphs = content.split('\n').filter(p => p.trim());
            paragraphs.forEach(p => {
                const para = document.createElement('p');
                para.textContent = p;
                contentDiv.appendChild(para);
            });
        }

        // Add sources if available
        if (sources && sources.length > 0) {
            const sourcesDiv = document.createElement('div');
            sourcesDiv.className = 'sources';

            const title = document.createElement('div');
            title.className = 'sources-title';
            title.textContent = '📚 Sumber:';
            sourcesDiv.appendChild(title);

            sources.forEach(src => {
                const item = document.createElement('span');
                item.className = 'source-item';
                item.textContent = src.source;
                sourcesDiv.appendChild(item);
            });

            contentDiv.appendChild(sourcesDiv);
        }

        // Add latency and cache indicator
        if (latency !== null) {
            const metaDiv = document.createElement('div');
            metaDiv.className = 'message-meta';
            metaDiv.innerHTML = `⚡ ${latency}s${cached ? ' <span class="cached-badge">📦 cached</span>' : ''}`;
            contentDiv.appendChild(metaDiv);
        }

        // Add feedback buttons for bot messages
        if (type === 'bot' && enableFeedback) {
            const feedbackDiv = document.createElement('div');
            feedbackDiv.className = 'feedback-buttons';
            feedbackDiv.innerHTML = `
                <button class="feedback-btn positive" onclick="sendFeedback(${messageIndex}, 'positive', this)" title="Jawaban membantu">👍</button>
                <button class="feedback-btn negative" onclick="sendFeedback(${messageIndex}, 'negative', this)" title="Jawaban kurang tepat">👎</button>
            `;
            contentDiv.appendChild(feedbackDiv);
        }

        messageDiv.appendChild(avatar);
        messageDiv.appendChild(contentDiv);
        chatMessages.appendChild(messageDiv);
    }

    // Send feedback
    window.sendFeedback = async function (msgIndex, feedback, btn) {
        const parentDiv = btn.parentElement;
        parentDiv.innerHTML = feedback === 'positive' ? '✅ Terima kasih!' : '📝 Terima kasih atas masukannya!';
        parentDiv.className = 'feedback-sent';

        // Get the message content
        const messageDiv = btn.closest('.message');
        const content = messageDiv.querySelector('.message-content p')?.textContent || '';

        try {
            await fetch('/api/feedback', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    session_id: sessionId,
                    message_index: msgIndex,
                    feedback: feedback,
                    response: content
                })
            });
        } catch (error) {
            console.error('Feedback error:', error);
        }
    };

    // Show/hide typing indicator
    function showTyping(show) {
        if (show) {
            typingIndicator.classList.remove('hidden');
        } else {
            typingIndicator.classList.add('hidden');
        }
    }

    // Scroll to bottom of chat
    function scrollToBottom() {
        const container = document.querySelector('.chat-container');
        container.scrollTop = container.scrollHeight;
    }

    // New chat
    async function newChat() {
        // Clear local storage
        localStorage.removeItem('chatSessionId');

        // Create new session
        const res = await fetch('/api/session/new', { method: 'POST' });
        const data = await res.json();
        sessionId = data.session_id;
        localStorage.setItem('chatSessionId', sessionId);
        sessionInfo.textContent = `Session: ${sessionId.substring(0, 8)}...`;

        // Clear messages except welcome
        const messages = chatMessages.querySelectorAll('.message');
        messages.forEach((msg, idx) => {
            if (idx > 0) msg.remove();
        });

        messageIndex = 0;
        addMessage('Chat baru dimulai! Silakan bertanya. 😊', 'bot', null, null);
    }

    // Refresh index
    async function refreshIndex() {
        refreshBtn.disabled = true;
        refreshBtn.textContent = '⏳ Loading...';

        try {
            const response = await fetch('/api/refresh', { method: 'POST' });
            const data = await response.json();

            if (data.message) {
                addMessage('✅ Index dokumen berhasil di-refresh!', 'bot', null, null);
            } else {
                addMessage('❌ Gagal refresh: ' + data.error, 'bot', null, null);
            }
        } catch (error) {
            addMessage('❌ Tidak dapat terhubung ke server.', 'bot', null, null);
        }

        refreshBtn.disabled = false;
        refreshBtn.textContent = '🔄 Refresh';
        scrollToBottom();
    }

    // Upload Modal Functions
    function openUploadModal() {
        uploadModal.classList.remove('hidden');
    }

    function closeUploadModalFn() {
        uploadModal.classList.add('hidden');
        uploadStatus.classList.add('hidden');
    }

    async function uploadFile(file) {
        uploadStatus.classList.remove('hidden');
        uploadStatus.innerHTML = '⏳ Mengupload...';
        uploadStatus.className = 'upload-status';

        const formData = new FormData();
        formData.append('file', file);

        try {
            const response = await fetch('/api/upload', {
                method: 'POST',
                body: formData
            });
            const data = await response.json();

            if (data.error) {
                uploadStatus.innerHTML = '❌ ' + data.error;
                uploadStatus.className = 'upload-status error';
            } else {
                uploadStatus.innerHTML = '✅ ' + data.message;
                uploadStatus.className = 'upload-status success';
                addMessage(`📄 File "${data.filename}" berhasil diupload! Klik Refresh untuk mengindex.`, 'bot', null, null);
            }
        } catch (error) {
            uploadStatus.innerHTML = '❌ Upload gagal';
            uploadStatus.className = 'upload-status error';
        }
    }

    // Event listeners
    sendBtn.addEventListener('click', sendMessage);

    messageInput.addEventListener('keypress', function (e) {
        if (e.key === 'Enter') {
            sendMessage();
        }
    });

    refreshBtn.addEventListener('click', refreshIndex);
    newChatBtn.addEventListener('click', newChat);
    uploadBtn.addEventListener('click', openUploadModal);
    closeUploadModal.addEventListener('click', closeUploadModalFn);
    selectFileBtn.addEventListener('click', () => fileInput.click());

    fileInput.addEventListener('change', (e) => {
        if (e.target.files.length > 0) {
            uploadFile(e.target.files[0]);
        }
    });

    // Drag and drop
    uploadZone.addEventListener('dragover', (e) => {
        e.preventDefault();
        uploadZone.classList.add('dragover');
    });

    uploadZone.addEventListener('dragleave', () => {
        uploadZone.classList.remove('dragover');
    });

    uploadZone.addEventListener('drop', (e) => {
        e.preventDefault();
        uploadZone.classList.remove('dragover');
        if (e.dataTransfer.files.length > 0) {
            uploadFile(e.dataTransfer.files[0]);
        }
    });

    // Close modal on outside click
    uploadModal.addEventListener('click', (e) => {
        if (e.target === uploadModal) {
            closeUploadModalFn();
        }
    });

    // Initialize
    messageInput.focus();
    initSession();
});
