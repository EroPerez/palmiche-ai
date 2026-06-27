<script setup>
import { ref, onMounted, nextTick } from 'vue'
import anime from 'animejs'
import SiriAnimation from './components/SiriAnimation.vue'

const messages = ref([])
const inputMessage = ref('')
const isConnected = ref(false)
const isTyping = ref(false)

// Voice feature states
const isTTSActive = ref(false)
const isListening = ref(false)

let ws = null
let currentAssistantMessageIndex = -1
let recognition = null

// Initialize Speech Recognition
const initSpeechRecognition = () => {
  const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition
  if (!SpeechRecognition) {
    console.warn("Speech Recognition API not supported in this browser.")
    return
  }
  
  recognition = new SpeechRecognition()
  recognition.lang = 'es-ES'
  recognition.interimResults = true // Mostrar resultados parciales mientras habla
  recognition.maxAlternatives = 1

  recognition.onstart = () => {
    isListening.value = true
  }

  recognition.onresult = (event) => {
    let finalTranscript = ''
    let interimTranscript = ''
    
    for (let i = event.resultIndex; i < event.results.length; ++i) {
      if (event.results[i].isFinal) {
        finalTranscript += event.results[i][0].transcript
      } else {
        interimTranscript += event.results[i][0].transcript
      }
    }
    
    // Si ya teníamos texto escrito antes de hablar, lo ideal sería concatenarlo, 
    // pero para este caso básico simplemente sobrescribimos con lo que se escucha
    // para que se vea como en Gemini.
    if (finalTranscript || interimTranscript) {
      inputMessage.value = finalTranscript + interimTranscript
    }
  }

  recognition.onerror = (event) => {
    console.error("Speech recognition error", event.error)
    stopListening()
  }

  recognition.onend = () => {
    stopListening()
    // Enviar automáticamente cuando termina de escuchar (si hay texto)
    if (inputMessage.value.trim() !== '') {
      sendMessage()
    }
  }
}

const toggleListening = () => {
  if (!recognition) {
    alert("Tu navegador no soporta reconocimiento de voz nativo (usa Chrome/Edge).")
    return
  }
  
  if (isListening.value) {
    recognition.stop()
  } else {
    recognition.start()
  }
}

const stopListening = () => {
  isListening.value = false
}

const speakText = (text) => {
  if (!isTTSActive.value || !window.speechSynthesis) return
  
  // Cancel previous speech if any
  window.speechSynthesis.cancel()
  
  const utterance = new SpeechSynthesisUtterance(text)
  utterance.lang = 'es-ES'
  // Puedes ajustar voz, rate, pitch aquí si lo deseas.
  window.speechSynthesis.speak(utterance)
}

const connectWebSocket = () => {
  ws = new WebSocket('ws://localhost:8000/ws/chat')

  ws.onopen = () => {
    isConnected.value = true
    messages.value.push({ role: 'system', content: 'Conectado a Jarvis Core.' })
  }

  ws.onmessage = (event) => {
    const data = JSON.parse(event.data)
    
    if (data.type === 'start') {
      isTyping.value = true
      messages.value.push({ role: 'assistant', content: '' })
      currentAssistantMessageIndex = messages.value.length - 1
    } 
    else if (data.type === 'stream') {
      if (currentAssistantMessageIndex !== -1) {
        messages.value[currentAssistantMessageIndex].content += data.content
        scrollToBottom()
      }
    } 
    else if (data.type === 'end') {
      isTyping.value = false
      if (currentAssistantMessageIndex !== -1) {
        const finalContent = data.content
        messages.value[currentAssistantMessageIndex].content = finalContent
        animateNewMessage(currentAssistantMessageIndex)
        speakText(finalContent)
      }
      currentAssistantMessageIndex = -1
      scrollToBottom()
    } 
    else if (data.type === 'error') {
      isTyping.value = false
      messages.value.push({ role: 'system', content: `Error: ${data.content}` })
      scrollToBottom()
    }
  }

  ws.onclose = () => {
    isConnected.value = false
    messages.value.push({ role: 'system', content: 'Desconectado del servidor. Reconectando...' })
    setTimeout(connectWebSocket, 3000)
  }
}

const sendMessage = () => {
  if (!inputMessage.value.trim() || !isConnected.value) return

  const userText = inputMessage.value.trim()
  messages.value.push({ role: 'user', content: userText })
  
  const msgObj = { message: userText, type: 'text' }
  ws.send(JSON.stringify(msgObj))
  
  inputMessage.value = ''
  
  nextTick(() => {
    animateNewMessage(messages.value.length - 1)
    scrollToBottom()
  })
}

const scrollToBottom = () => {
  nextTick(() => {
    const container = document.querySelector('.chat-messages')
    if (container) {
      container.scrollTop = container.scrollHeight
    }
  })
}

const animateNewMessage = (index) => {
  anime({
    targets: `.msg-${index}`,
    translateY: [20, 0],
    opacity: [0, 1],
    duration: 500,
    easing: 'easeOutExpo'
  })
}

onMounted(() => {
  connectWebSocket()
  initSpeechRecognition()
})
</script>

<template>
  <div class="chat-container">
    <header class="chat-header">
      <div class="header-left">
        <h1>Jarvis Web UI</h1>
        <span class="status" :class="{ connected: isConnected }">
          {{ isConnected ? 'Online' : 'Offline' }}
        </span>
      </div>
      <div class="header-right">
        <label class="tts-toggle" title="Jarvis hablará sus respuestas">
          <input type="checkbox" v-model="isTTSActive" />
          <span class="toggle-label">🔊 Voz de Jarvis</span>
        </label>
      </div>
    </header>

    <div class="chat-messages">
      <div 
        v-for="(msg, index) in messages" 
        :key="index"
        :class="['message-bubble', `role-${msg.role}`, `msg-${index}`]"
      >
        <div class="message-content">{{ msg.content }}</div>
      </div>
      <div v-if="isTyping" class="message-bubble role-assistant typing-indicator">
        Jarvis está pensando...
      </div>
    </div>

    <!-- Siri Animation Container -->
    <SiriAnimation :isListening="isListening" />

    <div class="chat-input-area">
      <button 
        class="mic-btn" 
        :class="{ active: isListening }"
        @click="toggleListening"
        title="Hablar con Jarvis"
      >
        🎤
      </button>
      <input 
        v-model="inputMessage" 
        @keyup.enter="sendMessage"
        type="text" 
        placeholder="Pregúntale a Jarvis..." 
        :disabled="!isConnected || isTyping"
      />
      <button class="send-btn" @click="sendMessage" :disabled="!isConnected || !inputMessage || isTyping">
        Enviar
      </button>
    </div>
  </div>
</template>

<style lang="scss" scoped>
.chat-container {
  --size-xs: 4px;
  --size-sm: 8px;
  --size-md: 12px;
  --size-lg: 16px;
  --size-xl: 20px;

  display: flex;
  flex-direction: column;
  height: calc(100vh - 3 * var(--size-sm));
  max-width: 800px;
  margin: var(--size-sm) auto;
  background-color: #121212;
  color: #fff;
  border: 3px solid #333;
  border-radius: var(--size-lg);
  overflow: hidden;
  position: relative;
}

.chat-header {
  padding: 1rem;
  background-color: #1a1a1a;
  border-bottom: 1px solid #333;
  display: flex;
  justify-content: space-between;
  align-items: center;

  h1 {
    margin: 0;
    font-size: 1.2rem;
    font-weight: 600;
  }
}

.header-left {
  display: flex;
  align-items: center;
  gap: 1rem;
}

.status {
  font-size: 0.8rem;
  padding: 0.25rem 0.5rem;
  border-radius: 12px;
  background-color: #dc3545;
  color: white;
}

.status.connected {
  background-color: #28a745;
}

.tts-toggle {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  cursor: pointer;
  font-size: 0.9rem;
  color: #ccc;
  user-select: none;
}
.tts-toggle input {
  cursor: pointer;
}

.chat-messages {
  flex: 1;
  overflow-y: auto;
  padding: 1rem;
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.message-bubble {
  max-width: 80%;
  padding: 0.75rem 1rem;
  border-radius: 12px;
  line-height: 1.4;
  word-wrap: break-word;
}

.role-user {
  align-self: flex-end;
  background-color: #0d6efd;
  color: white;
  border-bottom-right-radius: 4px;
}

.role-assistant {
  align-self: flex-start;
  background-color: #2a2a2a;
  color: #e0e0e0;
  border-bottom-left-radius: 4px;
}

.role-system {
  align-self: center;
  background-color: transparent;
  color: #888;
  font-size: 0.85rem;
  text-align: center;
}

.typing-indicator {
  font-style: italic;
  color: #aaa;
}


.chat-input-area {
  padding: 1rem;
  background-color: #1a1a1a;
  border-top: 1px solid #333;
  display: flex;
  gap: 0.5rem;
  align-items: center;
}

.mic-btn {
  background-color: #2a2a2a;
  border: 1px solid #444;
  border-radius: 50%;
  width: 45px;
  height: 45px;
  display: flex;
  justify-content: center;
  align-items: center;
  font-size: 1.2rem;
  cursor: pointer;
  transition: all 0.3s;
}

.mic-btn.active {
  background-color: #dc3545;
  border-color: #dc3545;
  box-shadow: 0 0 10px rgba(220, 53, 69, 0.5);
}

.chat-input-area input {
  flex: 1;
  padding: 0.75rem 1rem;
  border-radius: 24px;
  border: 1px solid #444;
  background-color: #2a2a2a;
  color: white;
  outline: none;
}

.chat-input-area input:focus {
  border-color: #0d6efd;
}

.send-btn {
  padding: 0.75rem 1.5rem;
  border-radius: 24px;
  border: none;
  background-color: #0d6efd;
  color: white;
  cursor: pointer;
  font-weight: 600;
  transition: background-color 0.2s;
}

.send-btn:hover:not(:disabled) {
  background-color: #0b5ed7;
}

.send-btn:disabled, .mic-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}
</style>
