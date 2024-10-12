import { createFileRoute } from "@tanstack/react-router";
import SignupPage from "@/pages/SignUpPage";

export const Route = createFileRoute("/signup")({
  component: SignupPage,
});
