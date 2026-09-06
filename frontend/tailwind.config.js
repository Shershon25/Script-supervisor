/** @type {import('tailwindcss').Config} */
module.exports = {
  darkMode: 'class',
  content: [
    './pages/**/*.{js,ts,jsx,tsx,mdx}',
    './components/**/*.{js,ts,jsx,tsx,mdx}',
    './app/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {
      colors: {
        app: 'var(--bg-app)',
        panel: 'var(--bg-panel)',
        card: 'var(--bg-card)',
        cardHover: 'var(--bg-card-hover)',
        screenplayPage: 'var(--bg-screenplay-page)',
        txtPrimary: 'var(--text-primary)',
        txtSecondary: 'var(--text-secondary)',
        txtMuted: 'var(--text-muted)',
        border: 'var(--border-color)',
        accent: {
          DEFAULT: '#6366f1',
          hover: '#4f46e5',
          light: '#818cf8',
          amber: '#d97706',
          emerald: '#10b981',
          rose: '#f43f5e',
        },
      },
    },
  },
  plugins: [],
};
