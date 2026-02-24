import type { Config } from "tailwindcss";
const config: Config = {
  content: ["./src/**/*.{js,ts,jsx,tsx,mdx}"],
  theme: {
    extend: {
      colors: {
        ide: {
          bg: "#0f172a",
          surface: "#1e293b",
          surface2: "#334155",
          border: "#334155",
          text: "#f8fafc",
          muted: "#94a3b8",
          accent: "#6366f1",
          success: "#10b981",
          warning: "#f59e0b",
          danger: "#ef4444",
          code: "#0d1117",
        },
      },
      fontFamily: {
        mono: ["JetBrains Mono", "Fira Code", "monospace"],
        sans: ["Inter", "system-ui", "sans-serif"],
      },
    },
  },
  plugins: [],
};
export default config;
