import { fetchEventSource } from "@microsoft/fetch-event-source";

import { Config } from "@/config";
import {
  AnthropicChatMessageOptions,
  OpenAIChatMessageOptions,
} from "@/lib/api/types.gen";

export async function streamingChat(
  sessionId: string,
  gpt_type: "anthropic" | "openai" = "anthropic",
  message: string,
  max_tokens: number = 100,
  onMessageUpdate: (content: string) => void
) {
  const accessToken = localStorage.getItem("access_token") || "";
  let requestBody: AnthropicChatMessageOptions | OpenAIChatMessageOptions;

  if (gpt_type === "anthropic") {
    requestBody = {
      max_tokens: max_tokens,
      messages: [
        {
          role: "user",
          content: message,
        },
      ],
      model: "claude-3-5-sonnet-20240620",
      stream: true,
    };
  } else {
    requestBody = {
      model: "gpt-4o-mini",
      messages: [{ role: "user", content: message }],
      stream: true,
    };
  }

  const url = `${Config.API_GPT_URL}/sessions/${sessionId}/messages?gpt_type=${gpt_type}`;

  await fetchEventSource(url, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Accept: "text/event-stream",
      Authorization: `Bearer ${accessToken}`,
    },
    body: JSON.stringify(requestBody),
    async onopen(res) {
      if (res.ok && res.status === 200) {
        console.log("Connection made ", res);
      } else if (res.status >= 400 && res.status < 500 && res.status !== 429) {
        console.log("Client-side error ", res);
      }
    },
    async onmessage(event) {
      try {
        const parsedData = JSON.parse(event.data);
        onMessageUpdate(parsedData.content);
      } catch (error) {
        console.error("Error parsing message:", error);
      }
    },
    async onclose() {
      console.log("Connection closed by the server");
    },
    onerror(err) {
      console.error("There was an error from server", err);
      throw err;
    },
  });
}
