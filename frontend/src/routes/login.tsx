import { createFileRoute } from "@tanstack/react-router";
import LoginPage from "@/app/auth/login";

export const Route = createFileRoute("/login")({
  component: LoginPage,
});
