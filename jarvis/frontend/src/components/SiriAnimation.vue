<script setup>
import { watch, ref, onBeforeUnmount } from 'vue'
import anime from 'animejs'

const props = defineProps({
  isListening: {
    type: Boolean,
    default: false,
  }
})

const containerRef = ref(null)
let audioContext = null
let analyser = null
let dataArray = null
let source = null
let animationId = null
let mediaStream = null

const startLiveWaveform = async () => {
  try {
    mediaStream = await navigator.mediaDevices.getUserMedia({ audio: true })
    audioContext = new (window.AudioContext || window.webkitAudioContext)()
    analyser = audioContext.createAnalyser()

    analyser.fftSize = 256
    const bufferLength = analyser.frequencyBinCount

    dataArray = new Uint8Array(bufferLength)
    source = audioContext.createMediaStreamSource(mediaStream)
    source.connect(analyser)
    animateWaves()
  } catch (err) {
    console.error('Error accediendo al micrófono:', err)
    startFakeAnimation()
  }
}

const animateWaves = () => {
  if (!analyser || !containerRef.value) {
    return
  }

  animationId = requestAnimationFrame(animateWaves)
  analyser.getByteFrequencyData(dataArray)

  const bins = [
    dataArray[2],
    dataArray[4],
    dataArray[8],
    dataArray[12],
    dataArray[16],
    dataArray[20],
    dataArray[24],
    dataArray[28],
    dataArray[32],
    dataArray[36]
  ]
  const waveElements = containerRef.value.querySelectorAll('.siri-wave')

  bins.forEach((value, index) => {
    const scale = 0.5 + (value / 255) * 2.5

    if (waveElements[index]) {
      waveElements[index].style.transform = `scaleY(${scale})`
      waveElements[index].style.transition = 'transform 0.05s ease-out'
    }
  })
}

const stopLiveWaveform = () => {
  if (animationId) {
    cancelAnimationFrame(animationId)
    animationId = null
  }

  if (mediaStream) {
    mediaStream.getTracks().forEach((track) => track.stop())
    mediaStream = null
  }

  if (audioContext) {
    audioContext.close()
    audioContext = null
  }

  if (containerRef.value) {
    const waveElements = containerRef.value.querySelectorAll('.siri-wave')

    waveElements.forEach((el) => {
      el.style.transform = 'scaleY(1)'
      el.style.transition = 'transform 0.3s ease-out'
    })
  }
}

let siriAnimation = null

const startFakeAnimation = () => {
  siriAnimation = anime({
    targets: '.siri-wave',
    scaleY: [
      {
        value: 2.5,
        duration: 400,
        easing: 'easeInOutSine'
      },
      {
        value: 0.5,
        duration: 400,
        easing: 'easeInOutSine'
      },
      {
        value: 1.5,
        duration: 400,
        easing: 'easeInOutSine'
      },
      {
        value: 1,
        duration: 400,
        easing: 'easeInOutSine'
      }
    ],
    delay: anime.stagger(100),
    loop: true,
    direction: 'alternate'
  })
}

const stopFakeAnimation = () => {

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
    startLiveWaveform()
  } else {
    stopLiveWaveform()
    stopFakeAnimation()
  }
})

onBeforeUnmount(() => {
  stopLiveWaveform()
  stopFakeAnimation()
})
</script>

<template>
  <div ref="containerRef" class="siri-container" v-show="isListening">
    <div class="siri-wave wave-1"></div>
    <div class="siri-wave wave-2"></div>
    <div class="siri-wave wave-3"></div>
    <div class="siri-wave wave-4"></div>
    <div class="siri-wave wave-5"></div>
    <div class="siri-wave wave-6"></div>
    <div class="siri-wave wave-7"></div>
    <div class="siri-wave wave-8"></div>
    <div class="siri-wave wave-9"></div>
    <div class="siri-wave wave-10"></div>
  </div>
</template>

<style lang="scss" scoped>
/* Animación Siri */
.siri-container {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 6px;
  height: 64px;
  padding: 0.5rem;
}

.siri-wave {
  width: 6px;
  height: 20px;
  border-radius: 3px;
}

.wave-1 {
  background-color: #ff3b30;
  box-shadow: 0 0 10px #ff3b30, 0 0 15px rgba(255, 59, 48, 0.5);
}

.wave-2 {
  background-color: #ff9500;
  box-shadow: 0 0 10px #ff9500, 0 0 15px rgba(255, 149, 0, 0.5);
}

.wave-3 {
  background-color: #4cd964;
  box-shadow: 0 0 10px #4cd964, 0 0 15px rgba(76, 217, 100, 0.5);
}

.wave-4 {
  background-color: #5ac8fa;
  box-shadow: 0 0 10px #5ac8fa, 0 0 15px rgba(90, 200, 250, 0.5);
}

.wave-5 {
  background-color: #007aff;
  box-shadow: 0 0 10px #007aff, 0 0 15px rgba(0, 122, 255, 0.5);
}

.wave-6 {
  background-color: #5856d6;
  box-shadow: 0 0 10px #5856d6, 0 0 15px rgba(88, 86, 214, 0.5);
}

.wave-7 {
  background-color: #ff2d55;
  box-shadow: 0 0 10px #ff2d55, 0 0 15px rgba(255, 45, 85, 0.5);
}

.wave-8 {
  background-color: #ffcc00;
  box-shadow: 0 0 10px #ffcc00, 0 0 15px rgba(255, 204, 0, 0.5);
}

.wave-9 {
  background-color: #af52de;
  box-shadow: 0 0 10px #af52de, 0 0 15px rgba(175, 82, 222, 0.5);
}

.wave-10 {
  background-color: #34c759;
  box-shadow: 0 0 10px #34c759, 0 0 15px rgba(52, 199, 89, 0.5);
}
</style>
