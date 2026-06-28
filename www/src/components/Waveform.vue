<script setup>
</script>

<template>
  <div class="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 z-40 flex items-center justify-center pointer-events-none drop-shadow-2xl scale-125">
    <div class="relative w-52 h-52 flex items-center justify-center">
      <!-- Glow trasero expansivo -->
      <div class="absolute inset-0 bg-cyan-600/30 blur-[40px] rounded-full animate-pulse duration-1000"></div>
      
      <!-- Detailed Waveform Ring 1 (Outer, fine details, cyan) -->
      <div class="absolute inset-0 rounded-full jarvis-audio-ring-1 shadow-[0_0_20px_rgba(6,182,212,0.5)_inset]"></div>
      
      <!-- Detailed Waveform Ring 2 (Middle, dense blocks, indigo) -->
      <div class="absolute inset-5 rounded-full jarvis-audio-ring-2 shadow-[0_0_15px_rgba(99,102,241,0.5)_inset]"></div>
      
      <!-- Detailed Waveform Ring 3 (Inner, fast pulse, bright cyan) -->
      <div class="absolute inset-10 rounded-full jarvis-audio-ring-3 shadow-[0_0_10px_rgba(34,211,238,0.6)_inset]"></div>

      <!-- Tech Dots / Particles rotating -->
      <div class="absolute inset-12 rounded-full jarvis-spin-slow mix-blend-screen">
         <div class="absolute top-0 left-1/2 w-2 h-2 bg-white rounded-full blur-[1px] shadow-[0_0_10px_white]"></div>
         <div class="absolute bottom-0 left-1/2 w-1.5 h-1.5 bg-cyan-300 rounded-full blur-[1px] shadow-[0_0_8px_cyan]"></div>
      </div>
      
      <div class="absolute inset-16 rounded-full jarvis-spin-reverse-fast mix-blend-screen">
         <div class="absolute right-0 top-1/2 w-2.5 h-2.5 bg-indigo-300 rounded-full blur-[1px] shadow-[0_0_12px_indigo]"></div>
      </div>

      <!-- Core / Orbita central -->
      <div class="absolute w-16 h-16 bg-gradient-to-tr from-cyan-300 via-cyan-500 to-indigo-600 rounded-full opacity-90 jarvis-core shadow-[0_0_50px_rgba(255,255,255,1),_0_0_20px_rgba(6,182,212,0.8)] blur-[1px]">
         <div class="absolute inset-2 bg-white/50 rounded-full blur-[3px]"></div>
         <!-- Core inner ping -->
         <div class="absolute inset-4 bg-white rounded-full animate-ping opacity-70" style="animation-duration: 0.8s"></div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.jarvis-spin-slow {
  animation: spin 8s linear infinite;
}
.jarvis-spin-reverse-fast {
  animation: spin-reverse 3s cubic-bezier(0.4, 0, 0.2, 1) infinite;
}

/* Outer ring: thin lines */
.jarvis-audio-ring-1 {
  background: repeating-conic-gradient(
    rgba(6, 182, 212, 0.9) 0deg,
    rgba(6, 182, 212, 0.9) 1deg,
    transparent 1deg,
    transparent 4deg
  );
  -webkit-mask: radial-gradient(transparent 68%, black 69%);
  mask: radial-gradient(transparent 68%, black 69%);
  animation: audio-pulse-1 1.5s ease-in-out infinite alternate, spin-reverse 20s linear infinite;
}

/* Middle ring: thicker blocks, indigo/cyan */
.jarvis-audio-ring-2 {
  background: repeating-conic-gradient(
    rgba(99, 102, 241, 0.8) 0deg,
    rgba(99, 102, 241, 0.8) 3deg,
    transparent 3deg,
    transparent 7deg
  );
  -webkit-mask: radial-gradient(transparent 64%, black 65%);
  mask: radial-gradient(transparent 64%, black 65%);
  animation: audio-pulse-2 0.8s ease-in-out infinite alternate, spin 12s linear infinite;
}

/* Inner ring: very dense */
.jarvis-audio-ring-3 {
  background: repeating-conic-gradient(
    rgba(34, 211, 238, 0.9) 0deg,
    rgba(34, 211, 238, 0.9) 2deg,
    transparent 2deg,
    transparent 4deg
  );
  -webkit-mask: radial-gradient(transparent 60%, black 61%);
  mask: radial-gradient(transparent 60%, black 61%);
  animation: audio-pulse-3 1.1s ease-in-out infinite alternate, spin-reverse 8s linear infinite;
}

.jarvis-core {
  animation: pulse-core 0.6s ease-in-out infinite alternate;
}

@keyframes spin {
  100% { transform: rotate(360deg); }
}

@keyframes spin-reverse {
  100% { transform: rotate(-360deg); }
}

@keyframes audio-pulse-1 {
  0% { transform: scale(0.98); opacity: 0.5; filter: drop-shadow(0 0 5px rgba(6, 182, 212, 0.5)); }
  100% { transform: scale(1.02); opacity: 1; filter: drop-shadow(0 0 15px rgba(6, 182, 212, 1)); }
}

@keyframes audio-pulse-2 {
  0% { transform: scale(0.95); opacity: 0.6; filter: drop-shadow(0 0 5px rgba(99, 102, 241, 0.5)); }
  100% { transform: scale(1.05); opacity: 1; filter: drop-shadow(0 0 20px rgba(99, 102, 241, 0.9)); }
}

@keyframes audio-pulse-3 {
  0% { transform: scale(0.92); opacity: 0.7; filter: drop-shadow(0 0 5px rgba(34, 211, 238, 0.5)); }
  100% { transform: scale(1.08); opacity: 1; filter: drop-shadow(0 0 25px rgba(34, 211, 238, 1)); }
}

@keyframes pulse-core {
  0% {
    transform: scale(0.85);
    opacity: 0.85;
    box-shadow: 0 0 30px rgba(6, 182, 212, 0.8), 0 0 10px rgba(99, 102, 241, 0.5) inset;
  }
  100% {
    transform: scale(1.15);
    opacity: 1;
    box-shadow: 0 0 60px rgba(255, 255, 255, 1), 0 0 30px rgba(99, 102, 241, 1), 0 0 20px rgba(255, 255, 255, 0.8) inset;
  }
}
</style>
