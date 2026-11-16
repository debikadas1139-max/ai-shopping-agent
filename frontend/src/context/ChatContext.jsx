import { createContext, useCallback, useContext, useMemo, useRef, useState } from "react";
import { sendChat } from "../services/api";
import { newId } from "../utils/format";

// Chat history lives here (not inside the chat page) so it survives moving between pages.
// It is kept in memory only: refreshing the browser starts a new conversation.
const ChatContext = createContext(null);
const MAX_HISTORY = 20;

export function ChatProvider({ children }) {
  const [messages, setMessages] = useState([]);
  const [loading, setLoading] = useState(false);
  const messagesRef = useRef([]);
  const busyRef = useRef(false);

  const push = useCallback((message) => {
    messagesRef.current = [...messagesRef.current, message];
    setMessages(messagesRef.current);
  }, []);

  const send = useCallback(
    async (text, imageId = null) => {
      const content = text.trim();
      if (!content || busyRef.current) return;
      busyRef.current = true;

      push({ id: newId(), role: "user", content });
      setLoading(true);

      // Send plain text plus the ids/names of products already shown, so "the first one" can be resolved.
      const history = messagesRef.current
        .filter((m) => !m.error)
        .slice(-MAX_HISTORY)
        .map((m) => ({
          role: m.role,
          content: m.content.slice(0, 4000),
          shown_products: [...(m.products || []), ...((m.comparison && m.comparison.products) || [])]
            .slice(0, 12)
            .map((p) => ({ id: p.id, name: p.name })),
        }));

      try {
        const data = await sendChat(history, imageId);
        push({
          id: newId(),
          role: "assistant",
          content: data.reply,
          products: data.products || [],
          comparison: data.comparison || null,
          orderProposal: data.order_proposal || null,
        });
      } catch (err) {
        push({ id: newId(), role: "assistant", content: err.message, error: true });
      } finally {
        busyRef.current = false;
        setLoading(false);
      }
    },
    [push]
  );

  const reset = useCallback(() => {
    messagesRef.current = [];
    setMessages([]);
  }, []);

  const value = useMemo(() => ({ messages, loading, send, reset }), [messages, loading, send, reset]);
  return <ChatContext.Provider value={value}>{children}</ChatContext.Provider>;
}

export function useChat() {
  const context = useContext(ChatContext);
  if (!context) throw new Error("useChat must be used inside <ChatProvider>");
  return context;
}
