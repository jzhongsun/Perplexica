/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./src/pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  darkMode: "class",
  theme: {
    extend: {
      colors: {
        light: {
          primary: "#FFFFFF",
          secondary: "#F7F7F7",
          100: "#EFEFEF",
          200: "#E6E6E6",
        },
        dark: {
          primary: "#000000",
          secondary: "#111111",
          100: "#1A1A1A",
          200: "#2B2B2B",
        },
      },
    },
  },
  plugins: [require("@tailwindcss/typography")],
} 