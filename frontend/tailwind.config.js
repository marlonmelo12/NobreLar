/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        nobre: {
          50: '#fffdf2',
          100: '#fff9c7',
          200: '#fff28f',
          300: '#ffe652',
          400: '#fed820',
          500: '#fdc700', // COR OFICIAL NOBRE LAR (#fdc700)
          600: '#d99f00',
          700: '#ad7200',
          800: '#8c5905',
          900: '#734808',
          950: '#432600',
        },
        brand: {
          DEFAULT: '#fdc700',
          hover: '#e5b300',
          active: '#cc9e00',
          light: '#fff8d6',
          dark: '#997300',
        }
      },
      boxShadow: {
        'nobre': '0 4px 20px -2px rgba(253, 199, 0, 0.25)',
      }
    },
  },
  plugins: [],
}
