/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
    "./pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        background: "#0b0f19",      // Deep obsidian space dark background
        card: "#131a2d",            // Sleek dark slate cards
        border: "#1e294b",          // Dark borders
        primary: "#06b6d4",         // Cyan accents
        secondary: "#10b981",       // Emerald online accents
        warning: "#f59e0b",         // Amber idle accents
        danger: "#ef4444",          // Rose offline accents
        muted: "#94a3b8",           // Soft slate text
      },
      boxShadow: {
        glass: "0 8px 32px 0 rgba(0, 0, 0, 0.37)"
      }
    },
  },
  plugins: [],
}
