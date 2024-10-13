import { createFileRoute } from "@tanstack/react-router";
// import ChatPage from '@/pages/ChatPage'
import React from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { Send, Loader2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Card, CardContent } from "@/components/ui/card";
import { getRouteApi } from "@tanstack/react-router";
import { GptService } from "@/lib/api/services.gen";
import { PublicChatSession } from "@/lib/api";

const route = getRouteApi("/chat/$chatId");

const ChatPage = () => {
  const { chatId } = route.useParams();
  const queryClient = useQueryClient();

  const { data: chatSession, isLoading } = useQuery<PublicChatSession, Error>({
    queryKey: ["chatSession", chatId],
    queryFn: async () => {
      const resp = await GptService.getSession({
        path: { session_id: chatId },
      });
      if (!resp.data) {
        throw Error("Failed to get chat session");
      }
      return resp.data;
    },
  });

  const chatMutation = useMutation({
    mutationFn: async (newMessage: string) => {
      await GptService.chat({
        body: { question: newMessage, role: "user" },
        path: { session_id: chatId },
      });
    },
    onSuccess: () => {
      // Refetch the chat session to get the updated messages
      queryClient.invalidateQueries({ queryKey: ["chatSession", chatId] });
    },
  });

  const handleSendMessage = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    const form = e.currentTarget;
    const formData = new FormData(form);
    const message = formData.get("message") as string;
    if (message.trim()) {
      await chatMutation.mutateAsync(message);
      form.reset();
    }
  };

  if (isLoading) {
    return (
      <div className="flex justify-center items-center h-screen">
        <Loader2 className="h-8 w-8 animate-spin" />
      </div>
    );
  }

  return (
    <div className="flex flex-col h-screen max-w-3xl mx-auto p-4">
      <h1 className="text-2xl font-bold mb-4">Chat Conversation</h1>
      <ScrollArea className="flex-grow mb-4">
        {chatSession?.messages.map((message, index) => (
          <Card
            key={index}
            className={`mb-2 ${message.role === "user" ? "ml-auto" : "mr-auto"}`}
          >
            <CardContent className="p-3">
              <p
                className={`text-sm ${message.role === "user" ? "text-blue-600" : "text-green-600"}`}
              >
                {message.role === "user" ? "You" : "AI"}
              </p>
              <p>{message.content}</p>
            </CardContent>
          </Card>
        ))}
      </ScrollArea>
      <form onSubmit={handleSendMessage} className="flex gap-2">
        <Input
          name="message"
          placeholder="Type your message..."
          className="flex-grow"
        />
        <Button type="submit" disabled={chatMutation.isPending}>
          {chatMutation.isPending ? (
            <Loader2 className="h-4 w-4 animate-spin" />
          ) : (
            <Send className="h-4 w-4" />
          )}
        </Button>
      </form>
    </div>
  );
};

export const Route = createFileRoute("/chat/$chatId")({
  component: ChatPage,
});
