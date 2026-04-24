/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        'primary': '#37352f',
        'secondary': '#9b9a97',
        'accent': '#03689b',
        'accent-secondary': '#448361',
        'surface': '#f7f6f3',
        'border': '#e3e2de',
        'success': '#448361',
        'warning': '#d9730d',
        'error': '#d44c47',
        'info': '#03689b',
        'highlight-yellow': '#fbf3db',
        'highlight-blue': '#ddebf1',
        'highlight-green': '#dbeddb',
        'highlight-red': '#ffe2dd',
        'highlight-purple': '#eae4f2',
        'neutral-warm': '#fbf6f3',
      },
      fontFamily: {
        'sans': ['Inter', 'system-ui', 'sans-serif'],
        'mono': ['JetBrains Mono', 'monospace'],
      },
      fontSize: {
        'h1': ['32px', { lineHeight: '1.2', fontWeight: '600' }],
        'h2': ['24px', { lineHeight: '1.3', fontWeight: '600' }],
        'h3': ['20px', { lineHeight: '1.4', fontWeight: '600' }],
      },
      spacing: {
        'xs': '4px',
        'sm': '8px',
        'md': '16px',
        'lg': '24px',
        'xl': '32px',
        '2xl': '48px',
      },
      borderRadius: {
        'sm': '4px',
        'md': '8px',
        'lg': '12px',
      },
    },
  },
  plugins: [],
}