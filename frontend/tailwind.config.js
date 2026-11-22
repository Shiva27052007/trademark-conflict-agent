/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  theme: {
    extend: {
      colors: {
        navy: {
          800: '#1a1f36',
          900: '#0f1225',
          950: '#0a0d1a',
        },
        charcoal: {
          700: '#2d3348',
          800: '#1e2235',
          900: '#141728',
        },
        cyan: {
          400: '#22d3ee',
          500: '#06b6d4',
          600: '#0891b2',
        },
      },
    },
  },
  plugins: [],
};
