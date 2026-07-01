<script setup>
// Componente sin estado, puramente visual
</script>

<template>
  <div class="absolute inset-0 z-50 flex flex-col items-center justify-center bg-zinc-900/95 backdrop-blur-md rounded-2xl overflow-hidden">
    <div class="relative flex items-center justify-center w-40 h-40 mb-12">
      <!-- Outer Ring -->
      <div class="absolute inset-0 border-2 border-cyan-500/20 rounded-full"></div>

      <!-- Dashed Rotating Ring -->
      <div class="absolute inset-[-10px] border-[3px] border-dashed border-cyan-400/40 rounded-full animate-[spin_8s_linear_infinite]"></div>

      <!-- Inner Fast Rotating Ring -->
      <div class="absolute inset-3 border-2 border-transparent border-t-cyan-300 border-b-cyan-300 rounded-full animate-[spin_3s_linear_infinite_reverse] shadow-[0_0_15px_rgba(103,232,249,0.5)]"></div>

      <!-- Core Glow -->
      <div class="w-16 h-16 bg-cyan-400 rounded-full blur-md animate-pulse"></div>
      <div class="absolute w-12 h-12 bg-white rounded-full shadow-[0_0_30px_rgba(34,211,238,1)]"></div>

      <!-- Tech lines -->
      <div class="absolute top-1/2 -left-12 w-8 h-[1px] bg-cyan-500/40"></div>
      <div class="absolute top-1/2 -right-12 w-8 h-[1px] bg-cyan-500/40"></div>
      <div class="absolute -top-12 left-1/2 w-[1px] h-8 bg-cyan-500/40"></div>
      <div class="absolute -bottom-12 left-1/2 w-[1px] h-8 bg-cyan-500/40"></div>
    </div>

    <div class="text-center font-mono">
      <h2 class="text-2xl text-cyan-300 tracking-[0.4em] font-bold mb-3 drop-shadow-[0_0_8px_rgba(103,232,249,0.8)] ml-[0.4em]">
        J.A.R.V.I.S
      </h2>
      <p class="text-cyan-500/80 tracking-[0.2em] text-sm flex items-center justify-center gap-3">
        <span class="w-2 h-2 rounded-full bg-cyan-400 animate-ping shadow-[0_0_8px_rgba(34,211,238,1)]"></span>
        ESTABLECIENDO CONEXIÓN...
      </p>
    </div>
  </div>
</template>
