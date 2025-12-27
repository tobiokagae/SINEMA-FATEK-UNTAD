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
                            Halo! 👋 Saya <span class="font-semibold text-amber-600">SINEMA Assistant</span>, asisten virtual untuk Sistem Informasi Ekstrakurikuler Mahasiswa.
                        </p>
                        <p class="text-sm text-gray-600 mt-2">Ada yang bisa saya bantu?</p>
                        
                        <!-- Quick Actions -->
                        <div class="mt-4 pt-3 border-t border-gray-100">
                            <p class="text-xs text-gray-500 font-medium mb-2">💡 Pertanyaan populer:</p>
                            <div class="flex flex-wrap gap-2">
                                <button @click="sendQuickMessage('Cara daftar SINEMA')"
                                        class="text-xs bg-amber-50 text-amber-700 px-3 py-1.5 rounded-full hover:bg-amber-100 transition-all duration-200 border border-amber-200/50 hover:shadow-sm">
                                    📝 Cara daftar
                                </button>
                                <button @click="sendQuickMessage('Info poin SINEMA')"
                                        class="text-xs bg-amber-50 text-amber-700 px-3 py-1.5 rounded-full hover:bg-amber-100 transition-all duration-200 border border-amber-200/50 hover:shadow-sm">
                                    ⭐ Info poin
                                </button>
                                <button @click="sendQuickMessage('Cek status pengajuan')"
                                        class="text-xs bg-amber-50 text-amber-700 px-3 py-1.5 rounded-full hover:bg-amber-100 transition-all duration-200 border border-amber-200/50 hover:shadow-sm">
                                    📊 Cek status
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

        addBotMessage(text) {
            const message = {
                type: 'bot',
                text: text,
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
                    this.addBotMessage('Maaf, terjadi kesalahan. Silakan coba lagi nanti. 😔');
                } else {
                    // Just use the response without sources
                    this.addBotMessage(data.response);
                }
            } catch (error) {
                console.error('Chatbot API error:', error);
                this.hideTyping();
                this.generateFallbackResponse(userMessage);
            }
        },
        
        getSessionId() {
            let sessionId = localStorage.getItem('sinema_chat_session');
            if (!sessionId) {
                sessionId = 'web_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
                localStorage.setItem('sinema_chat_session', sessionId);
            }
            return sessionId;
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

            this.addBotMessage(response);
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
                div.innerHTML = `
                    <div class="bg-gradient-to-br from-amber-500 to-amber-600 text-white rounded-xl p-2 flex-shrink-0 shadow-lg">
                        <svg class="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                            <path fill-rule="evenodd" d="M18 10c0 3.866-3.582 7-8 7a8.841 8.841 0 01-4.083-.98L2 17l1.338-3.123C2.493 12.767 2 11.434 2 10c0-3.866 3.582-7 8-7s8 3.134 8 7zM7 9H5v2h2V9zm8 0h-2v2h2V9zM9 9h2v2H9V9z" clip-rule="evenodd"/>
                        </svg>
                    </div>
                    <div class="flex flex-col max-w-[85%]">
                        <div class="bg-white rounded-2xl rounded-tl-md p-3 shadow-sm border border-gray-100">
                            <p class="text-sm text-gray-800 leading-relaxed">${this.formatMessage(message.text)}</p>
                        </div>
                        <span class="text-[10px] text-gray-400 mt-1">${this.formatTime(message.timestamp)}</span>
                    </div>
                `;
            }

            return div;
        },

        formatMessage(text) {
            return text
                .replace(/\n/g, '<br>')
                .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
                .replace(/\*(.*?)\*/g, '<em>$1</em>')
                .replace(/(\d+️⃣)/g, '<span class="text-amber-600">$1</span>');
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