<script setup>
import { computed } from 'vue'
import { marked } from 'marked'

const props = defineProps({
  msg: {
    type: Object,
    required: true
  },
  index: {
    type: Number,
    required: true
  }
})

const parsedContent = computed(() => {
  if (props.msg.role === 'assistant') {
    return marked.parse(props.msg.content)
  }

  return props.msg.content
})
</script>

<template>
  <div 
    :class="[
      'max-w-[85%] px-4 py-3 rounded-2xl leading-relaxed break-words shadow-sm text-lg',
      `msg-${index}`,
      msg.role === 'user'
        ? 'self-end bg-indigo-600 text-white rounded-br-sm'
        : msg.role === 'assistant'
            ? 'self-start bg-zinc-800 text-zinc-100 rounded-bl-sm border border-zinc-700/50 prose prose-invert prose-cyan prose-p:leading-relaxed prose-pre:bg-zinc-900 prose-pre:border prose-pre:border-zinc-700 max-w-none'
            : 'self-center bg-transparent text-zinc-500 text-sm text-center shadow-none',
    ]"
  >
    <div
      v-if="msg.role === 'assistant'"
      class="message-content"
      v-html="parsedContent"
    >
    </div>
    <div v-else class="message-content">{{ msg.content }}</div>
  </div>
</template>
