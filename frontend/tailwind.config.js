/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./src/**/*.{js,jsx,ts,tsx}",
    "./public/index.html"
  ],
  theme: {
    extend: {
      colors: {
        'trust-green': '#10B981',
        'caution-yellow': '#F59E0B',
        'danger-red': '#EF4444',
        'dark-blue': '#1E40AF',
        'light-gray': '#F8FAFC',
        'medium-gray': '#64748B'
      },
      fontFamily: {
        'sans': ['Inter', 'system-ui', 'sans-serif'],
      },
      animation: {
        'thermometer-fill': 'thermometer-fill 2s ease-out forwards',
        'pulse-slow': 'pulse 3s infinite',
        'bounce-subtle': 'bounce-subtle 2s infinite',
      },
      keyframes: {
        'thermometer-fill': {
          '0%': { height: '0%' },
          '100%': { height: 'var(--fill-height)' }
        },
        'bounce-subtle': {
          '0%, 100%': { transform: 'translateY(0)' },
          '50%': { transform: 'translateY(-5px)' }
        }
      }
    },
  },
  plugins: [],
}