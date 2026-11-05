import axios from "axios";

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || "http://127.0.0.1:8000/api",
});

export interface ChatResponse {
  response: string;
}

export interface HistoryMessage {
  role: "user" | "assistant";
  content: string;
}

export const sendChatMessage = async (
  input: string,
  history: HistoryMessage[] = [],
): Promise<string> => {
  const response = await api.post<ChatResponse>("/chat", {
    input,
    history,
  });
  return response.data.response;
};
