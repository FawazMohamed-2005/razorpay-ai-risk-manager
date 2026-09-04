/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        razorblue: {
          50: '#f0f7ff',
          100: '#e0effe',
          500: '#0c83ff',
          600: '#0066f5',
          700: '#0052cc',
          900: '#0a2540'
        }
      }
    },
  },
  plugins: [],
}
