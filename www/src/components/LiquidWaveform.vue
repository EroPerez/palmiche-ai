<script setup>
</script>

<template>
  <div class="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 z-40 flex items-center justify-center pointer-events-none drop-shadow-2xl">
    <div class="relative w-28 h-28 flex items-center justify-center">
      <!-- Glow trasero -->
      <div class="absolute inset-0 bg-cyan-500/30 blur-2xl rounded-full animate-pulse"></div>
      <!-- Liquid Blob 1 -->
      <div class="absolute w-24 h-24 bg-gradient-to-tr from-cyan-600 to-indigo-500 opacity-60 liquid-blob-1 mix-blend-screen shadow-[0_0_30px_rgba(6,182,212,0.8)]"></div>
      <!-- Liquid Blob 2 -->
      <div class="absolute w-20 h-20 bg-gradient-to-bl from-cyan-400 to-indigo-400 opacity-80 liquid-blob-2 mix-blend-screen"></div>
      <!-- Liquid Blob 3 (Core) -->
      <div class="absolute w-14 h-14 bg-cyan-200 opacity-90 liquid-blob-3 shadow-[0_0_20px_rgba(255,255,255,0.8)] blur-[1px]"></div>
    </div>
  </div>
</template>

<style scoped>
.liquid-blob-1 {
  animation: liquid-1 3s ease-in-out infinite alternate;
  border-radius: 40% 60% 70% 30% / 40% 50% 60% 50%;
}
.liquid-blob-2 {
  animation: liquid-2 2.2s ease-in-out infinite alternate-reverse;
  border-radius: 60% 40% 30% 70% / 60% 30% 70% 40%;
}
.liquid-blob-3 {
  animation: liquid-3 1.8s ease-in-out infinite alternate;
  border-radius: 50% 50% 40% 60% / 50% 40% 60% 50%;
}

@keyframes liquid-1 {
  0% {
    transform: scale(0.9) rotate(0deg);
    border-radius: 40% 60% 70% 30% / 40% 50% 60% 50%;
  }
  50% {
    transform: scale(1.15) rotate(90deg);
    border-radius: 60% 40% 30% 70% / 60% 30% 70% 40%;
  }
  100% {
    transform: scale(0.95) rotate(180deg);
    border-radius: 50% 70% 40% 60% / 40% 60% 50% 40%;
  }
}

@keyframes liquid-2 {
  0% {
    transform: scale(1) rotate(0deg);
    border-radius: 60% 40% 30% 70% / 60% 30% 70% 40%;
  }
  50% {
    transform: scale(1.25) rotate(-90deg);
    border-radius: 40% 60% 70% 30% / 40% 50% 60% 50%;
  }
  100% {
    transform: scale(0.85) rotate(-180deg);
    border-radius: 50% 50% 40% 60% / 50% 40% 60% 50%;
  }
}

@keyframes liquid-3 {
  0% {
    transform: scale(0.8) rotate(0deg);
    border-radius: 50% 50% 40% 60% / 50% 40% 60% 50%;
  }
  50% {
    transform: scale(1.35) rotate(45deg);
    border-radius: 60% 40% 70% 30% / 60% 50% 40% 70%;
  }
  100% {
    transform: scale(0.9) rotate(90deg);
    border-radius: 40% 60% 50% 50% / 40% 60% 40% 60%;
  }
}
</style>
