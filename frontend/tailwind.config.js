/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        bg: {
          base: '#0B0F17',
          surface: '#111726',
          elevated: '#161F33',
          card: '#0E1524',
          hover: '#1B2640',
          active: '#202E4C',
        },
        border: {
          subtle: '#1E2A42',
          DEFAULT: '#253552',
          highlight: '#3B4E73',
          ai: '#6366F1', // Indigo / Purple for AI hypotheses (dashed)
          evidence: '#10B981', // Emerald for runtime evidence (solid)
        },
        text: {
          primary: '#F1F5F9',
          secondary: '#94A3B8',
          muted: '#64748B',
          inverse: '#0B0F17',
        },
        severity: {
          critical: '#EF4444',
          high: '#F97316',
          medium: '#F59E0B',
          low: '#3B82F6',
          info: '#64748B',
        },
        status: {
          confirmed: '#10B981',
          reproduced: '#06B6D4',
          likely: '#F59E0B',
          potential: '#818CF8',
          unverified: '#94A3B8',
          falsePositive: '#64748B',
          verified: '#10B981',
          regression: '#EF4444',
        },
        brand: {
          50: '#EEF2FF',
          500: '#6366F1',
          600: '#4F46E5',
          700: '#4338CA',
          cyan: '#06B6D4',
        }
      },
      fontFamily: {
        sans: ['Inter', '-apple-system', 'BlinkMacSystemFont', 'Segoe UI', 'Roboto', 'sans-serif'],
        mono: ['JetBrains Mono', 'Fira Code', 'Roboto Mono', 'Menlo', 'Monaco', 'Courier New', 'monospace'],
      },
      borderWidth: {
        '1': '1px',
      }
    },
  },
  plugins: [],
}
