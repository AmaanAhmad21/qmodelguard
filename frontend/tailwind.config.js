/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        ink: {
          950: "#0a0a0b",
          900: "#0f0f10",
          800: "#0F172A",
          700: "#111C33",
        },
        neon: {
          500: "#22D3EE",
          600: "#06B6D4",
        },
        aurora: {
          500: "#A78BFA",
        },
        mint: {
          500: "#34D399",
        },
      },
      boxShadow: {
        "glow-sm": "0 0 0 1px rgba(255,255,255,0.06), 0 0 40px rgba(34,211,238,0.10)",
        "glow-md": "0 0 0 1px rgba(255,255,255,0.08), 0 0 80px rgba(167,139,250,0.12)",
      },
    },
  },
  plugins: [],
}
