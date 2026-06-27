<script setup>
import { ref, onMounted, nextTick, computed } from 'vue'
import anime from 'animejs'
import SiriAnimation from './components/SiriAnimation.vue'
import ChatMessage from './components/ChatMessage.vue'
import TypingIndicator from './components/TypingIndicator.vue'
import ConnectingOverlay from './components/ConnectingOverlay.vue'

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

const btnListenClasses = computed(() => {
  return isListening.value
    ? 'bg-rose-500 border-rose-500 shadow-[0_0_15px_rgba(244,63,94,0.4)] text-white scale-110'
    : 'bg-zinc-700 border-zinc-600 hover:bg-zinc-600 text-zinc-300'
})

const isConnectedClasses = computed(() => {
  return isConnected.value
    ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30'
    : 'bg-rose-500/20 text-rose-400 border border-rose-500/30'
})

// Initialize Speech Recognition
const initSpeechRecognition = () => {
  const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition

  if (!SpeechRecognition) {
    console.warn('Speech Recognition API not supported in this browser.')
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
    alert('Tu navegador no soporta reconocimiento de voz nativo (usa Chrome/Edge).')
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

  if (!isTTSActive.value || !window.speechSynthesis) {
    return
  }

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

    switch (data.type) {
      case 'start':
        isTyping.value = true
        messages.value.push({ role: 'assistant', content: '' })
        currentAssistantMessageIndex = messages.value.length - 1
        break
      case 'stream':
        if (currentAssistantMessageIndex !== -1) {
          messages.value[currentAssistantMessageIndex].content += data.content
          scrollToBottom()
        }
        break
      case 'end':
        isTyping.value = false
        if (currentAssistantMessageIndex !== -1) {
          const finalContent = data.content
          messages.value[currentAssistantMessageIndex].content = finalContent
          animateNewMessage(currentAssistantMessageIndex)
          speakText(finalContent)
        }
        currentAssistantMessageIndex = -1
        scrollToBottom()
        break
      case 'error':
        isTyping.value = false
        messages.value.push({ role: 'system', content: `Error: ${data.content}` })
        scrollToBottom()
        break
    }
  }

  ws.onclose = () => {
    isConnected.value = false
    messages.value.push({ role: 'system', content: 'Desconectado del servidor. Reconectando...' })
    setTimeout(connectWebSocket, 3000)
  }
}

const sendMessage = () => {
  if (!inputMessage.value.trim() || !isConnected.value) {
    return
  }

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
  <div class="flex flex-col h-[calc(100vh-24px)] container max-w-[60%] mx-auto bg-zinc-900 text-white border border-zinc-700/50 rounded-2xl overflow-hidden shadow-2xl relative">
    <Transition
      enter-active-class="transition-opacity duration-700"
      leave-active-class="transition-opacity duration-700"
      enter-from-class="opacity-0"
      leave-to-class="opacity-0"
    >
      <ConnectingOverlay v-if="!isConnected" />
    </Transition>

    <!-- Header with Glassmorphism -->
    <header class="p-4 bg-zinc-800/80 backdrop-blur-md border-b border-zinc-700/50 flex justify-between items-center z-10 sticky top-0">
      <div class="flex items-center gap-4">
        <h1 class="m-0 text-xl font-semibold bg-gradient-to-r from-blue-400 to-indigo-400 bg-clip-text text-transparent">
          Jarvis UI
        </h1>
        <span
          class="text-xs px-2.5 py-1 rounded-full font-medium transition-colors duration-300" 
          :class="isConnectedClasses"
        >
          {{ isConnected ? 'Online' : 'Offline' }}
        </span>
      </div>
      <div class="flex items-center">
        <label
          class="flex items-center gap-2 cursor-pointer text-sm text-zinc-400 hover:text-zinc-200 transition-colors select-none"
          title="Jarvis hablará sus respuestas"
        >
          <input type="checkbox" v-model="isTTSActive" class="accent-indigo-500 w-4 h-4 rounded cursor-pointer" />
          <span class="flex items-center gap-1 text-lg">
            <svg viewBox="0 0 24 24" fill="currentColor" width="22px" height="22px">
              <path d="M22 14H21C21 10.13 17.87 7 14 7H13V5.73C13.6 5.39 14 4.74 14 4C14 2.9 13.11 2 12 2S10 2.9 10 4C10 4.74 10.4 5.39 11 5.73V7H10C6.13 7 3 10.13 3 14H2C1.45 14 1 14.45 1 15V18C1 18.55 1.45 19 2 19H3V20C3 21.11 3.9 22 5 22H19C20.11 22 21 21.11 21 20V19H22C22.55 19 23 18.55 23 18V15C23 14.45 22.55 14 22 14M9.79 16.5C9.4 15.62 8.53 15 7.5 15S5.6 15.62 5.21 16.5C5.08 16.19 5 15.86 5 15.5C5 14.12 6.12 13 7.5 13S10 14.12 10 15.5C10 15.86 9.92 16.19 9.79 16.5M18.79 16.5C18.4 15.62 17.5 15 16.5 15S14.6 15.62 14.21 16.5C14.08 16.19 14 15.86 14 15.5C14 14.12 15.12 13 16.5 13S19 14.12 19 15.5C19 15.86 18.92 16.19 18.79 16.5Z" />
            </svg>
            Voz de Jarvis
          </span>
        </label>
      </div>
    </header>

    <!-- Chat Messages -->
    <div class="flex-1 overflow-y-auto p-4 flex flex-col gap-4 bg-zinc-900/50">
      <ChatMessage
        v-for="(msg, index) in messages"
        :key="index"
        :msg="msg"
        :index="index"
      />
      <TypingIndicator v-if="isTyping" />
    </div>

    <!-- Siri Animation Container -->
    <SiriAnimation :isListening="isListening" />

    <!-- Input Area -->
    <div class="p-4 bg-zinc-800/90 border-t border-zinc-700/50 flex gap-3 items-center backdrop-blur-md">
      <button
        :class="[
          'flex-shrink-0 w-11 h-11 flex justify-center items-center rounded-full text-xl transition-all duration-300 border disabled:opacity-50 disabled:cursor-not-allowed',
          btnListenClasses,
        ]"
        @click="toggleListening"
        title="Hablar con Jarvis"
        :disabled="!isConnected || isTyping"
      >
        <svg viewBox="0 0 24 24" fill="currentColor" width="26px" height="26px">
          <path d="M12,2A3,3 0 0,1 15,5V11A3,3 0 0,1 12,14A3,3 0 0,1 9,11V5A3,3 0 0,1 12,2M19,11C19,14.53 16.39,17.44 13,17.93V21H11V17.93C7.61,17.44 5,14.53 5,11H7A5,5 0 0,0 12,16A5,5 0 0,0 17,11H19Z" />
        </svg>
      </button>
      <input
        v-model="inputMessage"
        @keyup.enter="sendMessage"
        type="text" 
        placeholder="Pregúntale a Jarvis..."
        :disabled="!isConnected || isTyping"
        class="flex-1 px-5 py-3 rounded-full bg-zinc-900 border border-zinc-700 text-zinc-100 placeholder-zinc-500 focus:outline-none focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 transition-all disabled:opacity-50 disabled:cursor-not-allowed shadow-inner"
      />
      <button
        @click="sendMessage"
        :disabled="!isConnected || !inputMessage || isTyping"
        class="px-6 py-3 rounded-full bg-indigo-600 text-white font-medium hover:bg-indigo-500 disabled:opacity-50 disabled:cursor-not-allowed disabled:hover:bg-indigo-600 transition-colors shadow-lg shadow-indigo-500/20"
      >
        Enviar
      </button>
    </div>
  </div>
</template>
