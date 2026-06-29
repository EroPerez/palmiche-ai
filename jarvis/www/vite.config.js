import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import { VitePWA } from 'vite-plugin-pwa'

export default defineConfig({
  plugins: [
    vue(),
    VitePWA({
      registerType: 'autoUpdate',
      manifest: {
        name: 'Palmiche JARVIS',
        short_name: 'JARVIS',
        description: 'Just A Rather Very Intelligent System',
        theme_color: '#18181b', // zinc-900 para que coincida con el tema oscuro
        background_color: '#09090b', // zinc-950
        display: 'standalone',
        icons: [
          {
            src: 'jarvis-icon.svg',
            sizes: 'any',
            type: 'image/svg+xml',
            purpose: 'any maskable'
          }
        ]
      },
      devOptions: {
        enabled: true
      }
    })
  ],
  server: {
    port: 3000,
    open: true
  }
})
