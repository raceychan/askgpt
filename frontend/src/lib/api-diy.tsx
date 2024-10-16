import { fetchEventSource } from "@microsoft/fetch-event-source";

import { Config } from "@/config";

export async function streamingChat(
  sessionId: string,
  message: string,
  setStreamingMessage: React.Dispatch<React.SetStateAction<string>>
) {
  const accessToken = localStorage.getItem("access_token") || "";

  await fetchEventSource(`${Config.API_GPT_URL}/openai/chat/${sessionId}`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Accept: "text/event-stream",
      Authorization: `Bearer ${accessToken}`,
    },
    body: JSON.stringify({ question: message, role: "user" }),
    async onopen(res) {
      if (res.ok && res.status === 200) {
        console.log("Connection made ", res);
      } else if (res.status >= 400 && res.status < 500 && res.status !== 429) {
        console.log("Client-side error ", res);
        throw new Error(`HTTP error! status: ${res.status}`);
      }
    },
    async onmessage(event) {
      try {
        const parsedData = JSON.parse(event.data);
        setStreamingMessage((prev) => prev + parsedData.content);
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
