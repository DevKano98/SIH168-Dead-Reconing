/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./mobile.html",
    "./docs.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        canvas: {
          base: "#F8FAFC",
          subtle: "#F1F5F9",
          card: "#FFFFFF",
          hover: "#F8FAFC",
        },
        ink: {
          primary: "#0F172A",
          secondary: "#334155",
          muted: "#64748B",
          faint: "#94A3B8",
        },
        border: {
          light: "#E2E8F0",
          subtle: "#EDF2F7",
          medium: "#CBD5E1",
          focus: "#93C5FD",
        },
        tech: {
          blue: "#2563EB",
          "blue-subtle": "#EFF6FF",
          "blue-border": "#BFDBFE",
          green: "#16A34A",
          "green-subtle": "#F0FDF4",
          amber: "#D97706",
          "amber-subtle": "#FFFBEB",
          "amber-border": "#FDE68A",
          red: "#DC2626",
          "red-subtle": "#FEF2F2",
          purple: "#7C3AED",
        },
      },
      fontFamily: {
        sans: [
          "Inter",
          "-apple-system",
          "BlinkMacSystemFont",
          '"Segoe UI"',
          "Roboto",
          "system-ui",
          "sans-serif",
        ],
        mono: [
          '"JetBrains Mono"',
          "ui-monospace",
          "SFMono-Regular",
          "Menlo",
          "Monaco",
          "Consolas",
          '"Liberation Mono"',
          "monospace",
        ],
      },
      boxShadow: {
        instrument: "0 1px 3px rgba(0, 0, 0, 0.05), 0 1px 2px rgba(0, 0, 0, 0.03)",
        card: "0 1px 2px 0 rgba(0, 0, 0, 0.05)",
        elevated: "0 4px 6px -1px rgba(0, 0, 0, 0.07), 0 2px 4px -2px rgba(0, 0, 0, 0.05)",
        panel: "0 10px 15px -3px rgba(0, 0, 0, 0.06), 0 4px 6px -4px rgba(0, 0, 0, 0.04)",
      },
    },
  },
  plugins: [],
};
