import React, { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { Send, Loader2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Card, CardContent } from "@/components/ui/card";
import { SessionsService } from "@/lib/api/services.gen";
import { PublicChatSession } from "@/lib/api";
import { Textarea } from "@/components/ui/textarea";
import { streamingChat } from "./chat-service";

import { useParams } from "@tanstack/react-router";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Input } from "@/components/ui/input";

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
                message.role === "user" ? "bg-blue-100" : "bg-white-100"
              } rounded-lg p-3 shadow-sm`}
            >
              <p
                className={`text-sm font-semibold mb-1 ${
                  message.role === "user" ? "text-blue-700" : "text-green-700"
                }`}
              >
                {message.role === "user" ? "" : "GPT"}
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
  onSendMessage: (
    message: string,
    gptType: "anthropic" | "openai",
    maxTokens: number
  ) => void;
  isLoading: boolean;
}> = ({ onSendMessage, isLoading }) => {
  const [gptType, setGptType] = useState<"anthropic" | "openai">("anthropic");
  const [maxTokens, setMaxTokens] = useState(1000);
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

  const handleSubmit = (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    const form = e.currentTarget;
    const formData = new FormData(form);
    const message = formData.get("message") as string;
    if (message.trim()) {
      onSendMessage(message, gptType, maxTokens);
      form.reset();
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && e.ctrlKey) {
      e.preventDefault();
      const message = textareaRef.current?.value.trim();
      if (message) {
        onSendMessage(message, gptType, maxTokens);
        if (textareaRef.current) {
          textareaRef.current.value = "";
          adjustTextareaHeight();
        }
      }
    }
  };

  return (
    <form onSubmit={handleSubmit} className="flex flex-col gap-2">
      <div className="flex gap-2">
        <Select
          value={gptType}
          onValueChange={(value: "anthropic" | "openai") => setGptType(value)}
        >
          <SelectTrigger className="w-[180px]">
            <SelectValue placeholder="Select GPT type" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="anthropic">Anthropic</SelectItem>
            <SelectItem value="openai">OpenAI</SelectItem>
          </SelectContent>
        </Select>
        <Input
          type="number"
          value={maxTokens}
          onChange={(e) => setMaxTokens(Number(e.target.value))}
          min={1}
          max={2000}
          className="w-[120px]"
          placeholder="Max tokens"
        />
      </div>
      <div className="flex gap-2 items-stretch">
        <Textarea
          ref={textareaRef}
          name="message"
          placeholder="Type your message..."
          className="resize-none overflow-hidden flex-grow"
          rows={1}
          onInput={adjustTextareaHeight}
          onKeyDown={handleKeyDown}
        />
        <Button type="submit" disabled={isLoading} className="self-end">
          {isLoading ? (
            <Loader2 className="h-4 w-4 animate-spin mr-2" />
          ) : (
            <Send className="h-4 w-4 mr-2" />
          )}
          {isLoading ? "Sending..." : "Send"}
        </Button>
      </div>
    </form>
  );
};

const ChatPage: React.FC = () => {
  const { chatId } = useParams({ from: "/chat/$chatId" });
  const queryClient = useQueryClient();

  const { data: chatSession, isLoading } = useQuery<PublicChatSession, Error>({
    queryKey: ["chatSession", chatId],
    queryFn: async () => {
      const resp = await SessionsService.getSession({
        path: { session_id: chatId },
      });
      if (resp.error) {
        throw Error("Failed to get chat session");
      }
      return resp.data;
    },
  });

  const [streamingMessage, setStreamingMessage] = useState("");

  type AddNewMessage = {
    newMessage: string;
    gptType: "anthropic" | "openai";
    maxTokens: number;
  };

  const chatMutation = useMutation({
    mutationFn: async (new_message: AddNewMessage) => {
      setStreamingMessage("");

      await streamingChat(
        chatId,
        new_message.gptType,
        new_message.newMessage,
        new_message.maxTokens,
        (content: string) => {
          setStreamingMessage((prev) => prev + content);
        }
      );
    },
    onSuccess: () => {
      // Refetch the chat session to get the updated messages
      queryClient.invalidateQueries({ queryKey: ["chatSession", chatId] });
      setStreamingMessage(""); // Clear streaming message after successful mutation
    },
  });

  const handleSendMessage = async (
    message: string,
    gptType: "anthropic" | "openai",
    maxTokens: number
  ) => {
    if (message.trim()) {
      await chatMutation.mutateAsync({
        newMessage: message,
        gptType: gptType,
        maxTokens: maxTokens,
      });
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
      <div className="h-full overflow-hidden p-4 pb-20">
        <ScrollArea className="h-[calc(100%-3rem)]">
          <MessageBox chatSession={chatSession} />
          {streamingMessage && (
            <div className="mt-4 bg-green-100 rounded-lg p-3 shadow-sm">
              <p className="text-sm font-semibold mb-1 text-green-700">AI</p>
              <p className="text-gray-800 whitespace-pre-wrap">
                {streamingMessage}
              </p>
            </div>
          )}
        </ScrollArea>
      </div>
      <div className="fixed bottom-0 left-0 right-0 p-4 bg-white border-t max-w-3xl mx-auto">
        <InputBox
          onSendMessage={handleSendMessage}
          isLoading={chatMutation.isPending}
        />
      </div>
    </div>
  );
};

export default ChatPage;
