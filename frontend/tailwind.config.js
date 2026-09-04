/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        bg: 'var(--bg)',
        surface: 'var(--surface)',
        'surface-raised': 'var(--surface-raised)',
        border: 'var(--border)',
        'border-soft': 'var(--border-soft)',
        ink: {
          DEFAULT: 'var(--ink)',
          soft: 'var(--ink-soft)',
          faint: 'var(--ink-faint)',
        },
        primary: {
          DEFAULT: 'var(--primary)',
          soft: 'var(--primary-soft)',
          hover: 'var(--primary-hover)',
        },
        low: {
          DEFAULT: 'var(--low)',
          bg: 'var(--low-bg)',
        },
        medium: {
          DEFAULT: 'var(--medium)',
          bg: 'var(--medium-bg)',
        },
        high: {
          DEFAULT: 'var(--high)',
          bg: 'var(--high-bg)',
        },
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', '-apple-system', 'sans-serif'],
        mono: ['"IBM Plex Mono"', 'ui-monospace', 'monospace'],
      },
      borderRadius: {
        sm: 'var(--radius-sm)',
        md: 'var(--radius-md)',
        lg: 'var(--radius-lg)',
      },
      boxShadow: {
        card: 'var(--shadow-card)',
        drawer: 'var(--shadow-drawer)',
      }
    },
  },
  plugins: [],
}
