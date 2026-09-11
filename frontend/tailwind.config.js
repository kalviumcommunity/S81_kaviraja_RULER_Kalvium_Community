/** @type {import('tailwindcss').Config} */
module.exports = {
  darkMode: 'class',
  content: [
    './app/**/*.{js,ts,jsx,tsx,mdx}',
    './components/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {
      colors: {
        oxford: '#002147',
        oxfordDark: '#001630',
        oxfordLight: '#083266',
        tan: '#D2B48C',
        tanDark: '#B8976C',
        tanLight: '#F5EFEB',
        tanMuted: '#E6D9C8',
        surface: '#FAF8F5',
        cardBorder: '#D8CCBD',
      },
      borderRadius: {
        DEFAULT: '12px',
        sm: '12px',
        md: '12px',
        lg: '12px',
        xl: '12px',
        '2xl': '12px',
        '3xl': '12px',
      },
      fontFamily: {
        sans: ['"Plus Jakarta Sans"', 'system-ui', '-apple-system', 'sans-serif'],
        mono: ['"JetBrains Mono"', 'monospace'],
      },
    },
  },
  plugins: [],
};
