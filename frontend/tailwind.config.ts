import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        app: "var(--bg-app)",
        panel: "var(--bg-panel)",
        background: "var(--bg-app)",
        card: "var(--bg-card)",
        cardHover: "var(--bg-card-hover)",
        border: "var(--border-color)",
        txtPrimary: "var(--text-primary)",
        txtSecondary: "var(--text-secondary)",
        txtMuted: "var(--text-muted)",
        txtScreenplay: "var(--text-screenplay)",
        primary: "#1A1C20",
        secondary: "#586274",
        tertiary: "#C87D32",
        neutral: "#767673",
        danger: "#B82C2C",
        accent: {
          DEFAULT: "var(--accent-tertiary)",
          hover: "#B06B28",
          light: "#D88F44",
          amber: "#C87D32",
          slate: "#586274",
          dark: "#1A1C20",
          emerald: "#2E7D32",
          rose: "#B82C2C"
        }
      },
      fontFamily: {
        courier: ["var(--font-courier)", "Courier Prime", "Courier New", "monospace"],
        sans: ["var(--font-sans)", "Inter", "sans-serif"],
      }
    },
  },
  plugins: [],
};
export default config;
