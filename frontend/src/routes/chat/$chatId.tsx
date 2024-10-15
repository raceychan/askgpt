import { createFileRoute } from "@tanstack/react-router";
import React, { useState, useRef } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { Send, Loader2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Card, CardContent } from "@/components/ui/card";
import { GptService } from "@/lib/api/services.gen";
import { PublicChatSession } from "@/lib/api";
import { Textarea } from "@/components/ui/textarea";
import { streamingChat } from "@/lib/api-diy";

const MessageBox: React.FC<{ chatSession?: PublicChatSession }> = ({
  chatSession,
}) => {
  if (!chatSession) {
    return (
      <Card className="min-h-[8rem] h-full flex items-center justify-center">
        <CardContent>
          <p className="text-red-600 font-semibold">
            Error: Chat session not found.
          </p>
        </CardContent>
      </Card>
    );
  }

  if (chatSession.messages.length === 0) {
    return (
      <Card className="min-h-[8rem] h-full flex items-center justify-center">
        <CardContent>
          <p className="text-gray-600 text-center text-xl font-medium">
            Ask a question to get started.
          </p>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className="min-h-[8rem] h-full">
      <CardContent className="p-4 space-y-4">
        {chatSession.messages.map((message, index) => (
          <div
            key={index}
            className={`flex ${message.role === "user" ? "justify-end" : "justify-start"}`}
          >
            <div
              className={`max-w-[70%] ${
                message.role === "user" ? "bg-blue-100" : "bg-green-100"
              } rounded-lg p-3 shadow-sm`}
            >
              <p
                className={`text-sm font-semibold mb-1 ${
                  message.role === "user" ? "text-blue-700" : "text-green-700"
                }`}
              >
                {message.role === "user" ? "You" : "AI"}
              </p>
              <p className="text-gray-800 whitespace-pre-wrap">
                {message.content}
              </p>
            </div>
          </div>
        ))}
      </CardContent>
    </Card>
  );
};

const InputBox: React.FC<{
  onSendMessage: (e: React.FormEvent<HTMLFormElement>) => void;
  isLoading: boolean;
}> = ({ onSendMessage, isLoading }) => {
  const textareaRef = React.useRef<HTMLTextAreaElement>(null);

  const adjustTextareaHeight = () => {
    const textarea = textareaRef.current;
    if (textarea) {
      textarea.style.height = "auto";
      textarea.style.height = `${textarea.scrollHeight}px`;
    }
  };

  React.useEffect(() => {
    adjustTextareaHeight();
  }, []);

  return (
    <form onSubmit={onSendMessage} className="flex flex-col gap-2">
      <Textarea
        ref={textareaRef}
        name="message"
        placeholder="Type your message..."
        className="resize-none overflow-hidden"
        rows={1}
        onInput={adjustTextareaHeight}
      />
      <Button type="submit" disabled={isLoading} className="self-end">
        {isLoading ? (
          <Loader2 className="h-4 w-4 animate-spin mr-2" />
        ) : (
          <Send className="h-4 w-4 mr-2" />
        )}
        {isLoading ? "Sending..." : "Send"}
      </Button>
    </form>
  );
};

const ChatPage = () => {
  const { chatId } = Route.useParams();
  const queryClient = useQueryClient();

  const { data: chatSession, isLoading } = useQuery<PublicChatSession, Error>({
    queryKey: ["chatSession", chatId],
    queryFn: async () => {
      const resp = await GptService.getSession({
        path: { session_id: chatId },
      });
      if (resp.error) {
        throw Error("Failed to get chat session");
      }
      return resp.data;
    },
  });

  const [streamingMessage, setStreamingMessage] = useState("");
  const streamingMessageRef = useRef("");

  const chatMutation = useMutation({
    mutationFn: async (newMessage: string) => {
      setStreamingMessage("");
      streamingMessageRef.current = "";

      await streamingChat(chatId, newMessage, setStreamingMessage);
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
  // TODO: only display chat session if chatSession is not empty
  return (
    <div className="relative h-full max-w-3xl mx-auto">
      {chatSession && chatSession.messages.length > 0 && (
        <div className="h-full overflow-hidden p-4 pb-20">
          <ScrollArea className="h-[calc(100%-3rem)]">
            <MessageBox chatSession={chatSession} />
            {streamingMessage && (
              <div className="mt-4">
                <strong>AI:</strong> {streamingMessage}
              </div>
            )}
          </ScrollArea>
        </div>
      )}
      <div className="fixed bottom-0 left-0 right-0 p-4 bg-white border-t max-w-3xl mx-auto">
        <InputBox
          onSendMessage={handleSendMessage}
          isLoading={chatMutation.isPending}
        />
      </div>
    </div>
  );
};

export const Route = createFileRoute("/chat/$chatId")({
  component: ChatPage,
});
