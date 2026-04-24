import vue from '@vitejs/plugin-vue'

export default {
  plugins: [vue()],
  server: {
    host: '0.0.0.0',
    port: 5173,
  },
}
