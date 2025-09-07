import type { Config } from 'tailwindcss'

export default {
  darkMode: ['class'],
  content: ['./index.html', './src/**/*.{ts,tsx,js,jsx}'],
  theme: {
    extend: {
      colors: {
        brand: {
          50: '#eef8ff',
          100: '#d9edff',
          200: '#bfe0ff',
          300: '#93ccff',
          400: '#5db0ff',
          500: '#2a90ff',
          600: '#0f6fe6',
          700: '#0a56b4',
          800: '#0d4a8f',
          900: '#103e72',
        },
      },
    },
  },
  plugins: [],
} satisfies Config
