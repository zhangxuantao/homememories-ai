/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  theme: {
    extend: {
      colors: {
        primary: '#f0c6c6',
        misty: '#e8eef5',
        text: {
          DEFAULT: '#8b7e8a',
          light: '#c4a0a0',
        },
        subtle: '#f7e8e8',
      },
      fontFamily: {
        sans: [
          '"PingFang SC"',
          '"Microsoft YaHei"',
          '"Noto Sans SC"',
          'system-ui',
          '-apple-system',
          'sans-serif',
        ],
      },
      borderRadius: {
        card: '12px',
        btn: '8px',
        pill: '20px',
      },
    },
  },
  plugins: [],
};
