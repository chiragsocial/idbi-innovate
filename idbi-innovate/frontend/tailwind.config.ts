import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./app/**/*.{ts,tsx}", "./components/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        ink: "#0f172a",
        brand: { DEFAULT: "#4f46e5", dark: "#4338ca", light: "#eef2ff" },
        rag: { green: "#16a34a", amber: "#d97706", red: "#dc2626" },
      },
      fontFamily: {
        sans: ["ui-sans-serif", "system-ui", "-apple-system", "Segoe UI", "Roboto", "Arial"],
      },
      boxShadow: {
        card: "0 1px 3px rgba(15,23,42,.08), 0 1px 2px rgba(15,23,42,.06)",
        lift: "0 10px 30px -10px rgba(15,23,42,.25)",
      },
    },
  },
  plugins: [],
};
export default config;
