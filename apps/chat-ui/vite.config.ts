import path from "path"
import tailwindcss from "@tailwindcss/vite"
import { aui } from "@assistant-ui/vite"
import viteReact from "@vitejs/plugin-react"
import { defineConfig } from "vite"

// https://vite.dev/config/
export default defineConfig({
  plugins: [aui(), viteReact(), tailwindcss()],
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "./src"),
    },
  },
})
