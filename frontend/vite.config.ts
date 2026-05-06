import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import { VitePWA } from 'vite-plugin-pwa';

export default defineConfig({
  plugins: [
    react(),
    VitePWA({
      registerType: 'autoUpdate',
      includeAssets: ['favicon.svg'],
      manifest: {
        name: 'HomeMemories AI - 家庭回忆',
        short_name: 'HomeMemories',
        description: '私人家庭照片管理系统',
        theme_color: '#f0c6c6',
        background_color: '#ffffff',
        display: 'standalone',
        start_url: '/',
        icons: [
          {
            src: 'favicon.svg',
            sizes: 'any',
            type: 'image/svg+xml',
          },
        ],
      },
      workbox: {
        globPatterns: ['**/*.{js,css,html,svg,png,jpg,webp}'],
        runtimeCaching: [
          {
            urlPattern: /^https?:\/\/localhost:8501\/media\/thumbs\/.*/,
            handler: 'CacheFirst',
            options: {
              cacheName: 'thumbnails',
              expiration: { maxEntries: 500, maxAgeSeconds: 30 * 24 * 60 * 60 },
            },
          },
        ],
      },
    }),
  ],
  server: {
    port: 5173,
    proxy: {
      '/api': 'http://localhost:8501',
      '/media': 'http://localhost:8501',
    },
  },
  build: {
    outDir: 'dist',
    sourcemap: true,
  },
});
