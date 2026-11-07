/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        'dark-bg': '#0f172a',
        'glass-panel': 'rgba(30, 41, 59, 0.7)',
        'glass-border': 'rgba(255, 255, 255, 0.1)',
      }
    },
  },
  plugins: [],
}
