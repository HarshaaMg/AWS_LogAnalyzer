/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./src/**/*.{js,jsx,ts,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        primary: '#3b82f6',
        secondary: '#8b5cf6',
        danger: '#ef4444',
        warning: '#f59e0b',
        success: '#10b981',
        dark: '#1f2937',
        darker: '#111827'
      }
    },
  },
  plugins: [],
}
