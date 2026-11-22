import { fileURLToPath, URL } from 'node:url'

import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import vueDevTools from 'vite-plugin-vue-devtools'

// Запити до API і сторінки входу передаються сайту Django. changeOrigin: false
// лишає заголовок Host 127.0.0.1:5173, як в Origin, - інакше Django відхилить
// вхід і POST (Origin checking failed).
const django = { target: 'http://127.0.0.1:8000', changeOrigin: false }

// https://vite.dev/config/
export default defineConfig({
  plugins: [vue(), vueDevTools()],
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url)),
    },
  },
  server: {
    host: '127.0.0.1',
    proxy: {
      '/api': django,
      '/accounts': django,
    },
  },
  build: {
    // Сталі назви: шаблон Django підключає /static/frontend/app.js і app.css
    rollupOptions: {
      output: {
        entryFileNames: 'app.js',
        chunkFileNames: '[name].js',
        assetFileNames: 'app[extname]',
      },
    },
  },
})
