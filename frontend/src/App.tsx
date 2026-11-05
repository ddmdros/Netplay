import React, { useState, useRef, useEffect } from "react";
import { Send, Bot, User, Gamepad2 } from "lucide-react";
import { sendChatMessage } from "./services/api";

interface Message {
  id: string;
  text: string;
  sender: "user" | "bot";
}

function App() {
  const [messages, setMessages] = useState<Message[]>([
    {
      id: "1",
      text: "Olá! Sou o assistente do NetPlay. Posso buscar informações de jogos, classificação etária e onde comprar. Como posso ajudar?",
      sender: "bot",
    },
  ]);
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);

  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, isLoading]);

  const handleSendMessage = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || isLoading) return;

    const userMessageText = input;
    setInput("");

    const newUserMessage: Message = {
      id: Date.now().toString(),
      text: userMessageText,
      sender: "user",
    };
    setMessages((prev) => [...prev, newUserMessage]);

    setIsLoading(true);

    try {
      const history = messages.slice(-10).map((m) => ({
        role: m.sender === "user" ? ("user" as const) : ("assistant" as const),
        content: m.text,
      }));
      const botResponseText = await sendChatMessage(
        userMessageText,
        history,
      );

      const newBotMessage: Message = {
        id: (Date.now() + 1).toString(),
        text: botResponseText,
        sender: "bot",
      };
      setMessages((prev) => [...prev, newBotMessage]);
    } catch (error) {
      console.error("Erro ao falar com a API do NetPlay:", error);
      setMessages((prev) => [
        ...prev,
        {
          id: Date.now().toString(),
          text: "Ops, tive um problema para me conectar ao servidor. Verifique se o back-end está ligado!",
          sender: "bot",
        },
      ]);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div
      style={{
        display: "flex",
        flexDirection: "column",
        height: "100vh",
        backgroundColor: "#111827",
        color: "#f3f4f6",
        fontFamily: "sans-serif",
      }}
    >
      {/* Header */}
      <header
        style={{
          display: "flex",
          alignItems: "center",
          gap: "12px",
          padding: "16px 24px",
          backgroundColor: "#1f2937",
          borderBottom: "1px solid #374151",
        }}
      >
        <Gamepad2 size={28} color="#10b981" />
        <h1 style={{ margin: 0, fontSize: "20px", fontWeight: 600, color: "#f9fafb" }}>
          NetPlay
        </h1>
      </header>

      <main
        style={{
          flex: 1,
          overflowY: "auto",
          padding: "24px",
          display: "flex",
          flexDirection: "column",
          gap: "16px",
        }}
      >
        {messages.map((msg) => (
          <div
            key={msg.id}
            style={{
              display: "flex",
              gap: "12px",
              maxWidth: "70%",
              alignSelf: msg.sender === "user" ? "flex-end" : "flex-start",
              flexDirection: msg.sender === "user" ? "row-reverse" : "row",
            }}
          >
            <div
              style={{
                width: "36px",
                height: "36px",
                borderRadius: "50%",
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                backgroundColor: msg.sender === "user" ? "#3b82f6" : "#10b981",
                flexShrink: 0,
              }}
            >
              {msg.sender === "user" ? (
                <User size={18} color="#fff" />
              ) : (
                <Bot size={18} color="#fff" />
              )}
            </div>

            <div
              style={{
                padding: "12px 16px",
                borderRadius: "12px",
                lineHeight: "1.5",
                fontSize: "15px",
                whiteSpace: "pre-wrap",
                backgroundColor: msg.sender === "user" ? "#2563eb" : "#1f2937",
                border: msg.sender === "user" ? "none" : "1px solid #374151",
                color: "#f3f4f6",
                textAlign: "left",
              }}
            >
              {msg.text}
            </div>
          </div>
        ))}

        {isLoading && (
          <div
            style={{ display: "flex", gap: "12px", alignSelf: "flex-start" }}
          >
            <div
              style={{
                width: "36px",
                height: "36px",
                borderRadius: "50%",
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                backgroundColor: "#10b981",
              }}
            >
              <Bot size={18} color="#fff" />
            </div>
            <div
              style={{
                padding: "12px 16px",
                borderRadius: "12px",
                backgroundColor: "#1f2937",
                border: "1px solid #374151",
                color: "#9ca3af",
              }}
            >
              NetPlay está consultando a vizinhança...
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </main>

      <footer
        style={{
          padding: "24px",
          backgroundColor: "#1f2937",
          borderTop: "1px solid #374151",
        }}
      >
        <form
          onSubmit={handleSendMessage}
          style={{
            display: "flex",
            gap: "12px",
            maxWidth: "800px",
            margin: "0 auto",
          }}
        >
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Pergunte sobre um jogo..."
            disabled={isLoading}
            style={{
              flex: 1,
              padding: "14px 16px",
              borderRadius: "8px",
              backgroundColor: "#111827",
              border: "1px solid #4b5563",
              color: "#f3f4f6",
              fontSize: "15px",
              outline: "none",
            }}
          />
          <button
            type="submit"
            disabled={isLoading || !input.trim()}
            style={{
              padding: "0 20px",
              borderRadius: "8px",
              backgroundColor: "#10b981",
              border: "none",
              color: "#fff",
              cursor: isLoading || !input.trim() ? "not-allowed" : "pointer",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              opacity: isLoading || !input.trim() ? 0.6 : 1,
              transition: "background-color 0.2s",
            }}
          >
            <Send size={18} />
          </button>
        </form>
      </footer>
    </div>
  );
}

export default App;
