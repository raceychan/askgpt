import path from "path";
import reactSwc from "@vitejs/plugin-react-swc";
import { defineConfig, loadEnv } from "vite";
import { TanStackRouterVite } from "@tanstack/router-plugin/vite";

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), "");

  return {
    plugins: [TanStackRouterVite(), reactSwc()],
    resolve: {
      alias: {
        "@": path.resolve(__dirname, "./src"),
      },
    },
    server: {
      host: env.VITE_FRONTEND_API_HOST || "localhost",
      port: parseInt(env.VITE_FRONTEND_API_PORT || "5173", 10),
    },
  };
});
