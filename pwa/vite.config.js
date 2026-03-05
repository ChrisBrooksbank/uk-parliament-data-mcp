import { defineConfig } from 'vite'
import { VitePWA } from 'vite-plugin-pwa'

export default defineConfig({
  plugins: [
    VitePWA({
      registerType: 'autoUpdate',
      manifest: {
        name: 'Hansard Semantic Search',
        short_name: 'Hansard Search',
        description: 'Search UK Parliament debates by meaning using in-browser AI',
        theme_color: '#1a3a5c',
        background_color: '#f4f1ec',
        display: 'standalone',
        start_url: '/',
        icons: [
          {
            src: 'icons/icon-192.png',
            sizes: '192x192',
            type: 'image/png'
          },
          {
            src: 'icons/icon-512.png',
            sizes: '512x512',
            type: 'image/png'
          }
        ]
      },
      workbox: {
        // Don't cache transformers.js ONNX models via workbox — they self-cache in Cache API
        globIgnores: ['**/*.onnx', '**/ort-wasm*', '**/ort-wasm-simd*'],
        runtimeCaching: [
          {
            urlPattern: /^https:\/\/hansard-api\.parliament\.uk\/.*/i,
            handler: 'NetworkFirst',
            options: {
              cacheName: 'hansard-api-cache',
              expiration: { maxEntries: 50, maxAgeSeconds: 60 * 60 }
            }
          }
        ]
      }
    })
  ],
  optimizeDeps: {
    // Must be excluded for ESM Web Worker compatibility
    exclude: ['@xenova/transformers']
  },
  worker: {
    format: 'es'
  }
})
