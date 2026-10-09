import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import tailwindcss from '@tailwindcss/vite';

export default defineConfig({
  // Pin the local dev server to IPv4; this avoids the localhost/IPv6 issue seen on this machine.
  server: { host: '127.0.0.1' },
  plugins: [react(), tailwindcss()],
});
