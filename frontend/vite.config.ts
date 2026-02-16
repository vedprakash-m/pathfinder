import { defineConfig, loadEnv } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'

// https://vitejs.dev/config/
export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), '')

  const config = {
    plugins: [react()],
    resolve: {
      alias: {
        '@': path.resolve(__dirname, './src'),
      },
    },
    server: {
      port: 3000,
    } as any,
    build: {
      outDir: 'dist',
      sourcemap: true,
    },
    test: {
      globals: true,
      environment: 'jsdom',
      setupFiles: './src/tests/setup.ts',
      testTimeout: 10000,
      pool: 'forks',
      onConsoleLog(log: string) {
        const suppressedMessages = [
          'was not wrapped in act(...)',
          'React Router Future Flag Warning',
          'React does not recognize the',
          'non-boolean attribute `initial`',
          'storage.setItem is not a function',
          'ReactDOMTestUtils.act',
        ];
        if (suppressedMessages.some((message) => log.includes(message))) {
          return false;
        }
      },
      coverage: {
        provider: 'v8',
        reporter: ['text', 'lcov'],
        include: ['src/**/*.{ts,tsx}'],
        exclude: [
          'src/tests/**',
          'src/**/*.test.{ts,tsx}',
          'src/**/*.d.ts',
          'src/main.tsx',
          'src/vite-env.d.ts',
        ],
        reportsDirectory: './coverage',
      },
    },
  }

  // Only add proxy if we don't have VITE_API_URL set
  if (!env.VITE_API_URL) {
    config.server.proxy = {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
    }
  }

  return config
})
