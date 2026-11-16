/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,jsx}"],
  theme: {
    extend: {
      colors: {
        ink: "#16231B",
        paper: "#F4F6F1",
        mist: "#DCE4D8",
        leaf: { DEFAULT: "#2D6A4F", deep: "#1F4D39", soft: "#E3EFE7" },
        honey: { DEFAULT: "#E0A526", deep: "#8A5F00", soft: "#FBF1D6" },
        berry: { DEFAULT: "#B23A32", soft: "#FBE9E7" },
      },
      fontFamily: {
        display: ['"Bricolage Grotesque"', "ui-sans-serif", "system-ui", "sans-serif"],
        sans: ["Figtree", "ui-sans-serif", "system-ui", "sans-serif"],
      },
    },
  },
  plugins: [],
};
