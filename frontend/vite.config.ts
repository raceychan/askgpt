import path from "path";
import reactSwc from "@vitejs/plugin-react-swc";
import { defineConfig } from "vite";
import { TanStackRouterVite } from "@tanstack/router-plugin/vite";

export default defineConfig({
  plugins: [TanStackRouterVite(), reactSwc()],
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "./src"),
    },
  },
  server: {
    host: process.env.HOST || "localhost",
    port: parseInt(process.env.PORT || "5173", 10),
  },
});
