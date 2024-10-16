import { createFileRoute } from "@tanstack/react-router";
import SettingsPage from "@/app/settings";

export const Route = createFileRoute("/settings")({
  component: SettingsPage,
});
