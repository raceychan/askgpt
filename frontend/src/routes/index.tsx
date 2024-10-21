import { createFileRoute } from "@tanstack/react-router";
import HomePage from "@/app/home";

export const Route = createFileRoute("/")({
  component: () => (
    <div className="p-4">
      <HomePage />
    </div>
  ),
});
