import { createFileRoute } from "@tanstack/react-router";
import ChatPage from "@/app/gpt/chat/chat-page";

export const Route = createFileRoute("/chat/$chatId")({
  component: ChatPage,
});
