<script setup>
defineProps({
  msg: {
    type: Object,
    required: true
  },
  index: {
    type: Number,
    required: true
  }
})
</script>

<template>
  <div 
    :class="[
      'max-w-[85%] px-4 py-3 rounded-2xl leading-relaxed break-words shadow-sm text-lg',
      `msg-${index}`,
      msg.role === 'user' ? 'self-end bg-indigo-600 text-white rounded-br-sm' :
      msg.role === 'assistant' ? 'self-start bg-zinc-800 text-zinc-100 rounded-bl-sm border border-zinc-700/50' :
      'self-center bg-transparent text-zinc-500 text-sm text-center shadow-none'
    ]"
  >
    <div class="message-content">{{ msg.content }}</div>
  </div>
</template>
