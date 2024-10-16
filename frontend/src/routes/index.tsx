import { createFileRoute } from "@tanstack/react-router";
import HomePage from "@/app/home";

export const Route = createFileRoute("/")({
  component: HomePage,
});
