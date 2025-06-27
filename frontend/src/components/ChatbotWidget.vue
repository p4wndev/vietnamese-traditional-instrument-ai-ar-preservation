<template>
    <div class="chatbot-container">
        <transition name="slide-fade">
            <div v-if="isOpen" class="chat-window" :class="{ maximized: isMaximized }">
                <div class="chat-header">
                    <h3>Trợ lý ảo</h3>
                    <div class="header-controls">
                        <button class="resize-btn" @click="toggleMaximize">
                            <svg v-if="!isMaximized" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24"
                                fill="currentColor">
                                <path
                                    d="M7 14H5v5h5v-2H7v-3zm-2-4h2V7h3V5H5v5zm12 7h-3v2h5v-5h-2v3zM14 5v2h3v3h2V5h-5z" />
                            </svg>
                            <svg v-else xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor">
                                <path
                                    d="M5 16h3v3h2v-5H5v2zm3-8H5v2h5V5H8v3zm6 11h2v-3h3v-2h-5v5zm2-11V5h-2v5h5V8h-3z" />
                            </svg>
                        </button>
                        <button class="close-btn" @click="closeChat"><i class="fa-solid fa-minus"></i></button>
                    </div>
                </div>

                <div ref="messagesContainer" class="chat-messages">
                    <div v-for="(msg, index) in messages" :key="index" :class="['message', msg.sender]">
                        <div class="avatar" v-if="msg.sender === 'bot'">🤖</div>
                        <div class="bubble">{{ msg.text }}</div>
                    </div>
                </div>

                <div class="chat-input">
                    <input v-model="newMessage" @keyup.enter="sendMessage" placeholder="Nhập tin nhắn..."
                        ref="messageInput">
                    <button @click="sendMessage">
                        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor">
                            <path d="M2.01 21L23 12 2.01 3 2 10l15 2-15 2z" />
                        </svg>
                    </button>
                </div>
            </div>
        </transition>

        <button class="chat-toggle" v-show="!isOpen" @click="toggleChat">
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor">
                <path
                    d="M20 2H4c-1.1 0-1.99.9-1.99 2L2 22l4-4h14c1.1 0 2-.9 2-2V4c0-1.1-.9-2-2-2zm-2 12H6v-2h12v2zm0-3H6V9h12v2zm0-3H6V6h12v2z" />
            </svg>
        </button>
    </div>
</template>

<script>
import RagService from "../services/rag.service";

export default {
    name: 'ChatbotWidget',
    data() {
        return {
            isOpen: false,
            isMaximized: false,
            newMessage: '',
            messages: [
                { text: 'Xin chào! Tôi có thể giúp gì cho bạn?', sender: 'bot' }
            ]
        }
    },
    methods: {
        toggleChat() {
            this.isOpen = !this.isOpen
            if (this.isOpen) {
                this.$nextTick(() => {
                    this.$refs.messageInput.focus()
                    this.scrollToBottom()
                })
            }
        },
        closeChat() {
            this.isOpen = false
            this.isMaximized = false
        },
        sendMessage() {
            if (this.newMessage.trim() === '') return

            // Thêm tin nhắn người dùng
            this.messages.push({
                text: this.newMessage,
                sender: 'user'
            })

            const userMessage = this.newMessage
            this.newMessage = ''

            this.$nextTick(() => {
                this.scrollToBottom()

                // Giả lập phản hồi từ bot sau 1 giây
                setTimeout(() => {
                    this.botResponse(userMessage)
                }, 1000)
            })
        },
        async botResponse(userMessage) {
            // Logic xử lý phản hồi
            const response = await RagService.ragAnswer(userMessage);
            this.messages.push({
                text: response.answer,
                sender: 'bot'
            })
            this.$nextTick(this.scrollToBottom)
        },
        scrollToBottom() {
            const container = this.$refs.messagesContainer
            if (container) {
                container.scrollTop = container.scrollHeight
            }
        },
        toggleMaximize() {
            this.isMaximized = !this.isMaximized;
            this.$nextTick(() => {
                this.scrollToBottom();
                if (this.isMaximized) {
                    this.$refs.messageInput.focus();
                }
            });
        }
    }
} 
</script>

<style scoped>
.chatbot-container {
    position: fixed;
    bottom: 25px;
    right: 25px;
    z-index: 1000;
    display: flex;
    flex-direction: column;
    align-items: flex-end;
}

/* Nút toggle */
.chat-toggle {
    width: 60px;
    height: 60px;
    border-radius: 50%;
    background: #4361ee;
    color: white;
    border: none;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
    cursor: pointer;
    display: flex;
    justify-content: center;
    align-items: center;
    /* transition: all 0.3s ease; */
    transition: opacity 0.3s ease, transform 0.3s ease;
    z-index: 1001;
}
 
/* Đảm bảo nút ẩn hoàn toàn khi không hiển thị */
.chat-toggle[style*="display: none"] {
    display: none !important;
}

.chat-toggle:hover {
    background: #3a56e0;
    transform: scale(1.05);
}

.chat-toggle:active {
    transform: scale(0.95);
}

.chat-toggle svg {
    width: 24px;
    height: 24px;
}

.chat-toggle span {
    font-size: 28px;
    line-height: 1;
}

.chat-toggle.active {
    background: #f72585;
}

/* Cửa sổ chat */
.chat-window {
    width: 320px;
    height: 420px;
    background: white;
    border-radius: 16px;
    box-shadow: 0 8px 30px rgba(0, 0, 0, 0.15);
    display: flex;
    flex-direction: column;
    margin-bottom: 15px;
    overflow: hidden;
    transition: all 0.3s ease;
}

/* Chế độ phóng to */
.chat-window.maximized {
    position: fixed;
    top: 50%;
    left: 50%;
    transform: translate(-50%, -50%);
    width: 90vw;
    height: 90vh;
    max-width: 1200px;
    max-height: 800px;
    z-index: 2000;
    margin: 0;
}

.chat-header {
    background: #4361ee;
    color: white;
    padding: 15px 20px;
    display: flex;
    justify-content: space-between;
    align-items: center;
}

.chat-header h3 {
    margin: 0;
    font-size: 18px;
    font-weight: 600;
}

.header-controls {
    display: flex;
    gap: 8px;
}

.resize-btn,
.close-btn {
    background: rgba(255, 255, 255, 0.2);
    border: none;
    color: white;
    font-size: 18px;
    cursor: pointer;
    padding: 0;
    width: 30px;
    height: 30px;
    display: flex;
    justify-content: center;
    align-items: center;
    border-radius: 50%;
    transition: background 0.2s;
}

.resize-btn:hover,
.close-btn:hover {
    background: rgba(255, 255, 255, 0.3);
}

.resize-btn svg {
    width: 16px;
    height: 16px;
}

.chat-messages {
    flex: 1;
    padding: 15px;
    overflow-y: auto;
    background: #f8f9fa;
    display: flex;
    flex-direction: column;
}

/* Điều chỉnh cho chế độ phóng to */
.chat-window.maximized .chat-messages {
    padding: 20px;
}

.message {
    display: flex;
    margin-bottom: 15px;
    max-width: 85%;
}

.message.user {
    align-self: flex-end;
}

.message.bot {
    align-self: flex-start;
}

.avatar {
    width: 32px;
    height: 32px;
    background: #e9ecef;
    border-radius: 50%;
    display: flex;
    justify-content: center;
    align-items: center;
    margin-right: 10px;
    flex-shrink: 0;
}

/* Điều chỉnh avatar khi phóng to */
.chat-window.maximized .avatar {
    width: 40px;
    height: 40px;
    font-size: 20px;
}

.bubble {
    padding: 12px 15px;
    border-radius: 18px;
    line-height: 1.4;
    font-size: 14px;
}

/* Điều chỉnh bong bóng khi phóng to */
.chat-window.maximized .bubble {
    padding: 15px 20px;
    font-size: 16px;
}

.message.user .bubble {
    background: #4361ee;
    color: white;
    border-bottom-right-radius: 5px;
}

.message.bot .bubble {
    background: #e9ecef;
    color: #333;
    border-bottom-left-radius: 5px;
}

.chat-input {
    display: flex;
    padding: 15px;
    background: white;
    border-top: 1px solid #e9ecef;
}

.chat-input input {
    flex: 1;
    padding: 12px 15px;
    border: 1px solid #dee2e6;
    border-radius: 24px;
    outline: none;
    font-size: 14px;
    transition: border 0.3s;
}

.chat-input input:focus {
    border-color: #4361ee;
}

.chat-input button {
    background: none;
    border: none;
    margin-left: 10px;
    cursor: pointer;
    color: #4361ee;
    display: flex;
    align-items: center;
    justify-content: center;
}

.chat-input button svg {
    width: 24px;
    height: 24px;
}

/* Hiệu ứng mở/đóng */
.slide-fade-enter-active,
.slide-fade-leave-active {
    transition: all 0.3s ease;
}

.slide-fade-enter,
.slide-fade-leave-to {
    transform: translateY(20px);
    opacity: 0;
}

/* Scrollbar styling */
.chat-messages::-webkit-scrollbar {
    width: 6px;
}

.chat-messages::-webkit-scrollbar-track {
    background: #f1f1f1;
    border-radius: 10px;
}

.chat-messages::-webkit-scrollbar-thumb {
    background: #c1c1c1;
    border-radius: 10px;
}

.chat-messages::-webkit-scrollbar-thumb:hover {
    background: #a8a8a8;
}

/* Nền mờ khi phóng to */
.chat-window.maximized {
    box-shadow: 0 20px 50px rgba(0, 0, 0, 0.3);
}
</style>