<script setup>
import { watch } from 'vue'
import anime from 'animejs'

const props = defineProps({
  isListening: {
    type: Boolean,
    default: false
  }
})

let siriAnimation = null

const startAnimation = () => {
  siriAnimation = anime({
    targets: '.siri-wave',
    scaleY: [
      { value: 2.5, duration: 400, easing: 'easeInOutSine' },
      { value: 0.5, duration: 400, easing: 'easeInOutSine' },
      { value: 1.5, duration: 400, easing: 'easeInOutSine' },
      { value: 1, duration: 400, easing: 'easeInOutSine' }
    ],
    delay: anime.stagger(100),
    loop: true,
    direction: 'alternate'
  })
}

const stopAnimation = () => {
  if (siriAnimation) {
    siriAnimation.pause()
    anime({
      targets: '.siri-wave',
      scaleY: 1,
      duration: 300,
      easing: 'easeOutQuad'
    })
  }
}

watch(() => props.isListening, (newVal) => {
  if (newVal) {
    startAnimation()
  } else {
    stopAnimation()
  }
})
</script>

<template>
  <div class="siri-container" v-show="isListening">
    <div class="siri-wave wave-1"></div>
    <div class="siri-wave wave-2"></div>
    <div class="siri-wave wave-3"></div>
    <div class="siri-wave wave-4"></div>
    <div class="siri-wave wave-5"></div>
  </div>
</template>

<style lang="scss" scoped>
/* Animación Siri */
.siri-container {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 6px;
  height: 40px;
  background-color: #1a1a1a;
  padding: 0.5rem;
  border-top: 1px solid #333;
}

.siri-wave {
  width: 6px;
  height: 20px;
  border-radius: 3px;
}
.wave-1 { background-color: #ff3b30; box-shadow: 0 0 10px #ff3b30, 0 0 15px rgba(255, 59, 48, 0.5); }
.wave-2 { background-color: #ff9500; box-shadow: 0 0 10px #ff9500, 0 0 15px rgba(255, 149, 0, 0.5); }
.wave-3 { background-color: #4cd964; box-shadow: 0 0 10px #4cd964, 0 0 15px rgba(76, 217, 100, 0.5); }
.wave-4 { background-color: #5ac8fa; box-shadow: 0 0 10px #5ac8fa, 0 0 15px rgba(90, 200, 250, 0.5); }
.wave-5 { background-color: #007aff; box-shadow: 0 0 10px #007aff, 0 0 15px rgba(0, 122, 255, 0.5); }
</style>
