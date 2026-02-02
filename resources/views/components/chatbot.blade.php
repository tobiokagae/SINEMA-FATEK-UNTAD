<!-- Chatbot Component - Enhanced UI -->
<div id="chatbot" x-data="chatbot()" x-init="init()"
     class="fixed bottom-4 right-4 sm:bottom-6 sm:right-6 z-50">

    <!-- Chat Button with pulse animation -->
    <button @click="toggleChat()"
            class="bg-gradient-to-r from-amber-500 to-amber-600 hover:from-amber-600 hover:to-amber-700 text-white rounded-full p-4 shadow-2xl transition-all duration-300 transform hover:scale-110 relative group"
            :class="{ 'ring-4 ring-amber-300/50 ring-offset-2': !isOpen }">
        
        <!-- Pulse ring when closed -->
        <div x-show="!isOpen" class="absolute inset-0 rounded-full bg-amber-500 animate-ping opacity-25"></div>
        
        <!-- Icon -->
        <svg x-show="!isOpen" class="w-7 h-7 relative z-10" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                  d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z">
            </path>
        </svg>
        <svg x-show="isOpen" class="w-7 h-7 relative z-10" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path>
        </svg>

        <!-- Unread badge -->
        <span x-show="!isOpen && unreadCount > 0"
              class="absolute -top-1 -right-1 bg-red-500 text-white text-xs rounded-full h-5 w-5 flex items-center justify-center font-bold animate-bounce shadow-lg"
              x-text="unreadCount"></span>
    </button>

    <!-- Chat Window -->
    <div x-show="isOpen"
         x-transition:enter="transition ease-out duration-300"
         x-transition:enter-start="opacity-0 scale-90 translate-y-4"
         x-transition:enter-end="opacity-100 scale-100 translate-y-0"
         x-transition:leave="transition ease-in duration-200"
         x-transition:leave-start="opacity-100 scale-100"
         x-transition:leave-end="opacity-0 scale-90"
         class="fixed inset-0 sm:absolute sm:inset-auto sm:bottom-20 sm:right-0 w-full sm:w-[380px] h-full sm:h-[520px] bg-white sm:rounded-2xl shadow-2xl flex flex-col overflow-hidden z-50 sm:border sm:border-gray-200/50">

        <!-- Header - Compact -->
        <div class="flex-shrink-0 bg-gradient-to-r from-amber-500 via-amber-500 to-amber-600 text-white px-3 py-2.5 flex items-center justify-between relative overflow-hidden">
            <!-- Decorative circles -->
            <div class="absolute top-0 right-0 w-16 h-16 bg-white/10 rounded-full -translate-y-8 translate-x-8"></div>
            
            <div class="flex items-center space-x-2.5 relative z-10">
                <div class="bg-white/20 backdrop-blur-sm rounded-lg p-1.5">
                    <svg class="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                        <path fill-rule="evenodd" d="M18 10c0 3.866-3.582 7-8 7a8.841 8.841 0 01-4.083-.98L2 17l1.338-3.123C2.493 12.767 2 11.434 2 10c0-3.866 3.582-7 8-7s8 3.134 8 7zM7 9H5v2h2V9zm8 0h-2v2h2V9zM9 9h2v2H9V9z" clip-rule="evenodd"/>
                    </svg>
                </div>
                <div>
                    <h3 class="font-semibold text-sm">SINEMA Assistant</h3>
                    <p class="text-[10px] opacity-90 flex items-center">
                        <span class="w-1.5 h-1.5 bg-green-400 rounded-full mr-1 animate-pulse"></span>
                        Online
                    </p>
                </div>
            </div>
            <button @click="toggleChat()" class="hover:bg-white/20 rounded-lg p-1.5 transition-all duration-200 relative z-10">
                <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path>
                </svg>
            </button>
        </div>

        <!-- Messages Area - Scrollable -->
        <div class="flex-1 overflow-y-auto p-4 space-y-4 bg-gradient-to-b from-amber-50/50 to-white" id="chatMessages">
            <!-- Welcome Message -->
            <div class="flex items-start space-x-3 animate-fade-in">
                <div class="bg-gradient-to-br from-amber-500 to-amber-600 text-white rounded-xl p-2 flex-shrink-0 shadow-lg">
                    <svg class="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                        <path fill-rule="evenodd" d="M18 10c0 3.866-3.582 7-8 7a8.841 8.841 0 01-4.083-.98L2 17l1.338-3.123C2.493 12.767 2 11.434 2 10c0-3.866 3.582-7 8-7s8 3.134 8 7zM7 9H5v2h2V9zm8 0h-2v2h2V9zM9 9h2v2H9V9z" clip-rule="evenodd"/>
                    </svg>
                </div>
                <div class="flex flex-col max-w-[85%]">
                    <div class="bg-white rounded-2xl rounded-tl-md p-4 shadow-sm border border-gray-100">
                        <p class="text-sm text-gray-800 leading-relaxed">
                            Halo! 👋 Saya <span class="font-semibold text-amber-600">SINEMA Assistant</span>, asisten virtual yang siap membantu Anda seputar kegiatan ekstrakurikuler, panduan akademik, dan tugas akhir di Fakultas Teknik UNTAD.
                        </p>
                        <p class="text-sm text-gray-600 mt-2">Ada yang bisa saya bantu?</p>
                        
                        <!-- Quick Actions -->
                        <div class="mt-4 pt-3 border-t border-gray-100">
                            <p class="text-xs text-gray-500 font-medium mb-2">💡 Pertanyaan populer:</p>
                            <div class="flex flex-wrap gap-2">
                                <button @click="sendQuickMessage('Bagaimana cara mengajukan kegiatan ekstrakurikuler?')"
                                        class="text-xs bg-amber-50 text-amber-700 px-3 py-1.5 rounded-full hover:bg-amber-100 transition-all duration-200 border border-amber-200/50 hover:shadow-sm">
                                    📝 Pengajuan kegiatan
                                </button>
                                <button @click="sendQuickMessage('Bagaimana cara menghitung nilai mutu ekstrakurikuler?')"
                                        class="text-xs bg-amber-50 text-amber-700 px-3 py-1.5 rounded-full hover:bg-amber-100 transition-all duration-200 border border-amber-200/50 hover:shadow-sm">
                                    ⭐ Nilai mutu
                                </button>
                                <button @click="sendQuickMessage('Apa syarat untuk mendapatkan transkrip TEM?')"
                                        class="text-xs bg-amber-50 text-amber-700 px-3 py-1.5 rounded-full hover:bg-amber-100 transition-all duration-200 border border-amber-200/50 hover:shadow-sm">
                                    📄 Transkrip TEM
                                </button>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <!-- Input Area -->
        <div class="border-t border-gray-100 p-4 bg-white">
            <form @submit.prevent="sendMessage()" class="flex items-center space-x-3">
                <div class="flex-1 relative">
                    <input x-model="inputMessage"
                           x-ref="chatInput"
                           @keydown.enter="sendMessage()"
                           type="text"
                           placeholder="Ketik pesan..."
                           class="w-full px-4 py-3 border border-gray-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-amber-500/50 focus:border-amber-500 text-sm bg-gray-50 hover:bg-white transition-colors duration-200 placeholder-gray-400">
                </div>
                <button type="submit"
                        :disabled="!inputMessage.trim()"
                        class="bg-gradient-to-r from-amber-500 to-amber-600 hover:from-amber-600 hover:to-amber-700 disabled:from-gray-300 disabled:to-gray-400 text-white p-3 rounded-xl transition-all duration-200 transform hover:scale-105 active:scale-95 shadow-lg hover:shadow-amber-500/30 disabled:shadow-none disabled:transform-none">
                    <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8"></path>
                    </svg>
                </button>
            </form>
            
            <!-- Powered by -->
            <div class="mt-3 text-center">
                <span class="text-[10px] text-gray-400">Powered by SINEMA RAG Chatbot</span>
            </div>
        </div>
    </div>
</div>

<!-- Marked.js for Markdown parsing -->
<script src="https://cdn.jsdelivr.net/npm/marked/marked.min.js"></script>

<!-- KaTeX for LaTeX math rendering -->
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/katex@0.16.9/dist/katex.min.css">
<script src="https://cdn.jsdelivr.net/npm/katex@0.16.9/dist/katex.min.js"></script>
<script src="https://cdn.jsdelivr.net/npm/katex@0.16.9/dist/contrib/auto-render.min.js"></script>

<style>
    @keyframes fade-in {
        from { opacity: 0; transform: translateY(10px); }
        to { opacity: 1; transform: translateY(0); }
    }
    .animate-fade-in {
        animation: fade-in 0.3s ease-out forwards;
    }
    
    /* Custom scrollbar for chat */
    #chatMessages::-webkit-scrollbar {
        width: 6px;
    }
    #chatMessages::-webkit-scrollbar-track {
        background: transparent;
    }
    #chatMessages::-webkit-scrollbar-thumb {
        background: #d4d4d4;
        border-radius: 3px;
    }
    #chatMessages::-webkit-scrollbar-thumb:hover {
        background: #a3a3a3;
    }
    
    /* Message formatting styles - Markdown Support */
    .chat-message {
        text-align: left;
        line-height: 1.7;
        font-size: 13px;
        color: #374151;
    }
    
    /* Headers */
    .chat-message h1, .chat-message h2, .chat-message h3 {
        font-weight: 600;
        color: #d97706;
        margin: 14px 0 8px 0;
    }
    .chat-message h1:first-child, .chat-message h2:first-child, .chat-message h3:first-child {
        margin-top: 0;
    }
    .chat-message h1 { font-size: 16px; }
    .chat-message h2 { font-size: 15px; }
    .chat-message h3 { font-size: 14px; }
    
    /* Bold & Italic */
    .chat-message strong { font-weight: 600; color: #111827; }
    .chat-message em { font-style: italic; }
    
    /* Paragraphs */
    .chat-message p {
        margin-bottom: 10px;
    }
    .chat-message p:last-child {
        margin-bottom: 0;
    }
    
    /* Ordered & Unordered Lists */
    .chat-message ol, .chat-message ul {
        margin: 8px 0 12px 0;
        padding-left: 20px;
    }
    .chat-message ol { list-style-type: decimal; }
    .chat-message ul { list-style-type: disc; }
    .chat-message li {
        margin-bottom: 6px;
        line-height: 1.6;
    }
    .chat-message li:last-child { margin-bottom: 0; }
    
    /* Nested Lists */
    .chat-message ol ol, .chat-message ul ul, .chat-message ol ul, .chat-message ul ol {
        margin: 4px 0;
        padding-left: 16px;
    }
    
    /* Code */
    .chat-message code {
        background: #f3f4f6;
        padding: 2px 6px;
        border-radius: 4px;
        font-size: 12px;
        font-family: monospace;
    }
    
    /* Blockquote */
    .chat-message blockquote {
        border-left: 3px solid #d97706;
        padding-left: 12px;
        margin: 8px 0;
        color: #6b7280;
        font-style: italic;
    }
</style>

<script>
function chatbot() {
    return {
        isOpen: false,
        inputMessage: '',
        messages: [],
        isTyping: false,
        unreadCount: 0,

        init() {
            this.messages = [];
        },

        toggleChat() {
            this.isOpen = !this.isOpen;
            if (this.isOpen) {
                this.unreadCount = 0;
                setTimeout(() => this.$refs.chatInput?.focus(), 100);
            }
        },

        sendMessage() {
            if (!this.inputMessage.trim()) return;

            const message = {
                type: 'user',
                text: this.inputMessage,
                timestamp: new Date().toISOString()
            };

            this.messages.push(message);
            this.inputMessage = '';
            this.renderMessages();

            this.showTyping();
            this.generateResponse(message.text);
        },

        sendQuickMessage(text) {
            this.inputMessage = text;
            this.sendMessage();
        },

        showTyping() {
            this.isTyping = true;
            // Add typing indicator to chat messages
            const chatMessages = document.getElementById('chatMessages');
            if (chatMessages) {
                // Remove existing typing indicator if any
                const existing = document.getElementById('typingIndicator');
                if (existing) existing.remove();
                
                // Create typing indicator element
                const typingDiv = document.createElement('div');
                typingDiv.id = 'typingIndicator';
                typingDiv.className = 'flex items-start space-x-3 animate-fade-in';
                typingDiv.innerHTML = `
                    <div class="bg-gradient-to-br from-amber-500 to-amber-600 text-white rounded-xl p-2 flex-shrink-0 shadow-lg">
                        <svg class="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                            <path fill-rule="evenodd" d="M18 10c0 3.866-3.582 7-8 7a8.841 8.841 0 01-4.083-.98L2 17l1.338-3.123C2.493 12.767 2 11.434 2 10c0-3.866 3.582-7 8-7s8 3.134 8 7zM7 9H5v2h2V9zm8 0h-2v2h2V9zM9 9h2v2H9V9z" clip-rule="evenodd"/>
                        </svg>
                    </div>
                    <div class="flex flex-col max-w-[85%]">
                        <div class="bg-white rounded-2xl rounded-tl-md px-4 py-3 shadow-sm border border-gray-100">
                            <div class="flex items-center space-x-2">
                                <div class="flex space-x-1">
                                    <div class="w-2 h-2 bg-amber-500 rounded-full animate-bounce" style="animation-delay: 0ms"></div>
                                    <div class="w-2 h-2 bg-amber-500 rounded-full animate-bounce" style="animation-delay: 150ms"></div>
                                    <div class="w-2 h-2 bg-amber-500 rounded-full animate-bounce" style="animation-delay: 300ms"></div>
                                </div>
                                <span class="text-xs text-gray-400">mengetik...</span>
                            </div>
                        </div>
                    </div>
                `;
                chatMessages.appendChild(typingDiv);
                chatMessages.scrollTop = chatMessages.scrollHeight;
            }
        },

        hideTyping() {
            this.isTyping = false;
            // Remove typing indicator from chat messages
            const typingIndicator = document.getElementById('typingIndicator');
            if (typingIndicator) {
                typingIndicator.remove();
            }
        },

        addBotMessage(text, sources = []) {
            const message = {
                type: 'bot',
                text: text,
                sources: sources,
                timestamp: new Date().toISOString()
            };

            this.messages.push(message);
            this.renderMessages();

            if (!this.isOpen) {
                this.unreadCount++;
            }
        },

        async generateResponse(userMessage) {
            const API_URL = 'http://localhost:5000/api/chat';
            
            try {
                const response = await fetch(API_URL, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        message: userMessage,
                        session_id: this.getSessionId()
                    })
                });
                
                this.hideTyping();
                
                if (!response.ok) {
                    throw new Error('API request failed');
                }
                
                const data = await response.json();
                
                if (data.error) {
                    this.addBotMessage('Maaf, terjadi kesalahan. Silakan coba lagi nanti. 😔', []);
                } else {
                    // Pass sources for citation feature
                    this.addBotMessage(data.response, data.sources || []);
                }
            } catch (error) {
                console.error('Chatbot API error:', error);
                this.hideTyping();
                this.generateFallbackResponse(userMessage);
            }
        },
        
        getSessionId() {
            // Generate new session ID on every page load (fresh start on refresh)
            if (!this._sessionId) {
                this._sessionId = 'web_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
            }
            return this._sessionId;
        },
        
        generateFallbackResponse(userMessage) {
            const lowerMessage = userMessage.toLowerCase();
            let response = '';

            if (lowerMessage.includes('halo') || lowerMessage.includes('hai')) {
                response = 'Halo! 👋 Selamat datang di SINEMA. Ada yang bisa saya bantu?';
            } else if (lowerMessage.includes('daftar') || lowerMessage.includes('registrasi')) {
                response = `Untuk mendaftar di SINEMA:\n\n1️⃣ Klik "Daftar Sekarang"\n2️⃣ Isi form pendaftaran\n3️⃣ Upload sertifikat PKKMB\n4️⃣ Verifikasi email\n5️⃣ Login dan mulai!`;
            } else if (lowerMessage.includes('poin') || lowerMessage.includes('skor')) {
                response = `💡 **Sistem Poin SINEMA:**\n\n🏆 Lomba: 100-500 poin\n📚 Seminar: 50-200 poin\n🤝 Kepanitiaan: 150-400 poin\n🌱 Pengabdian: 200-600 poin`;
            } else {
                response = `Maaf, server sedang tidak tersedia. 😅\n\nSilakan coba lagi nanti atau hubungi admin.`;
            }

            this.addBotMessage(response, []);
        },

        renderMessages() {
            const chatMessages = document.getElementById('chatMessages');
            if (!chatMessages) return;

            while (chatMessages.children.length > 1) {
                chatMessages.removeChild(chatMessages.lastChild);
            }

            this.messages.forEach(msg => {
                const messageEl = this.createMessageElement(msg);
                chatMessages.appendChild(messageEl);
            });

            chatMessages.scrollTop = chatMessages.scrollHeight;
        },

        createMessageElement(message) {
            const div = document.createElement('div');
            div.className = `flex items-start space-x-3 animate-fade-in ${message.type === 'user' ? 'flex-row-reverse space-x-reverse' : ''}`;

            if (message.type === 'user') {
                div.innerHTML = `
                    <div class="bg-gradient-to-br from-amber-500 to-amber-600 text-white rounded-xl p-2 flex-shrink-0 shadow-lg">
                        <svg class="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                            <path fill-rule="evenodd" d="M10 9a3 3 0 100-6 3 3 0 000 6zm-7 9a7 7 0 1114 0H3z" clip-rule="evenodd"/>
                        </svg>
                    </div>
                    <div class="flex flex-col max-w-[75%]">
                        <div class="bg-gradient-to-br from-amber-500 to-amber-600 text-white rounded-2xl rounded-tr-md p-3 shadow-lg">
                            <p class="text-sm leading-relaxed">${this.formatMessage(message.text)}</p>
                        </div>
                        <span class="text-[10px] text-gray-400 mt-1 text-right">${this.formatTime(message.timestamp)}</span>
                    </div>
                `;
            } else {
                // Build sources HTML if available
                let sourcesHtml = '';
                if (message.sources && message.sources.length > 0) {
                    let sourceItems = '';
                    for (let idx = 0; idx < message.sources.length; idx++) {
                        const src = message.sources[idx];
                        const borderClass = idx > 0 ? 'border-t border-gray-100' : '';
                        const headingHtml = src.heading ? '<div class="text-xs text-amber-600 font-medium">📌 ' + src.heading + '</div>' : '';
                        const snippetHtml = src.snippet ? '<div class="text-xs text-gray-500 italic mt-0.5">"' + src.snippet + '"</div>' : '';
                        sourceItems += '<div class="py-2 ' + borderClass + '"><div class="text-xs font-medium text-gray-700 break-all">📄 ' + src.source + '</div>' + headingHtml + snippetHtml + '</div>';
                    }
                    
                    sourcesHtml = '<div class="mt-2 pt-2 border-t border-gray-100"><details><summary class="text-xs text-amber-600 hover:text-amber-700 font-medium cursor-pointer">📚 Lihat Sumber (' + message.sources.length + ')</summary><div class="mt-2 bg-amber-50 rounded-lg p-2 text-left">' + sourceItems + '</div></details></div>';
                }
                
                div.innerHTML = '<div class="bg-gradient-to-br from-amber-500 to-amber-600 text-white rounded-xl p-2 flex-shrink-0 shadow-lg"><svg class="w-4 h-4" fill="currentColor" viewBox="0 0 20 20"><path fill-rule="evenodd" d="M18 10c0 3.866-3.582 7-8 7a8.841 8.841 0 01-4.083-.98L2 17l1.338-3.123C2.493 12.767 2 11.434 2 10c0-3.866 3.582-7 8-7s8 3.134 8 7zM7 9H5v2h2V9zm8 0h-2v2h2V9zM9 9h2v2H9V9z" clip-rule="evenodd"/></svg></div><div class="flex flex-col max-w-[85%] overflow-hidden"><div class="bg-white rounded-2xl rounded-tl-md p-3 shadow-sm border border-gray-100 overflow-hidden"><div class="text-sm text-gray-800 leading-relaxed break-words">' + this.formatMessage(message.text) + '</div>' + sourcesHtml + '</div><span class="text-[10px] text-gray-400 mt-1">' + this.formatTime(message.timestamp) + '</span></div>';
            }

            return div;
        },

        formatMessage(text) {
            // Process LaTeX BEFORE markdown to prevent escaping
            let processedText = text;
            const mathPlaceholders = [];
            
            // Extract display math ($$...$$) and replace with placeholders
            processedText = processedText.replace(/\$\$([\s\S]*?)\$\$/g, (match, latex) => {
                const placeholder = `%%MATH_DISPLAY_${mathPlaceholders.length}%%`;
                mathPlaceholders.push({ type: 'display', latex: latex.trim() });
                return placeholder;
            });
            
            // Extract inline math ($...$) and replace with placeholders
            processedText = processedText.replace(/\$([^\$\n]+?)\$/g, (match, latex) => {
                const placeholder = `%%MATH_INLINE_${mathPlaceholders.length}%%`;
                mathPlaceholders.push({ type: 'inline', latex: latex.trim() });
                return placeholder;
            });
            
            // Now parse markdown
            let html = processedText;
            if (typeof marked !== 'undefined') {
                marked.setOptions({
                    breaks: true,
                    gfm: true,
                    sanitize: false
                });
                html = marked.parse(processedText);
            }
            
            // Replace placeholders with rendered KaTeX
            if (typeof katex !== 'undefined') {
                mathPlaceholders.forEach((item, index) => {
                    const placeholderDisplay = `%%MATH_DISPLAY_${index}%%`;
                    const placeholderInline = `%%MATH_INLINE_${index}%%`;
                    
                    try {
                        const rendered = katex.renderToString(item.latex, {
                            displayMode: item.type === 'display',
                            throwOnError: false
                        });
                        html = html.replace(placeholderDisplay, rendered);
                        html = html.replace(placeholderInline, rendered);
                    } catch (e) {
                        // If KaTeX fails, show original
                        html = html.replace(placeholderDisplay, `$$${item.latex}$$`);
                        html = html.replace(placeholderInline, `$${item.latex}$`);
                    }
                });
            }
            
            return '<div class="chat-message">' + html + '</div>';
        },

        formatTime(timestamp) {
            return new Date(timestamp).toLocaleTimeString('id-ID', {
                hour: '2-digit',
                minute: '2-digit'
            });
        }
    }
}
</script>