import { createFileRoute } from "@tanstack/react-router";
import ChatRootPage from "@/app/gpt/chat/chat-root";

export const Route = createFileRoute("/chat/")({
  component: ChatRootPage,
});
