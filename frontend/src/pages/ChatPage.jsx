import { useEffect, useRef, useState } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import { Camera, Leaf, RotateCcw, Send } from "lucide-react";
import ChatMessage from "../components/ChatMessage";
import { useChat } from "../context/ChatContext";

const SUGGESTIONS = [
  { label: "Find organic honey under $20.", text: "Find organic honey under $20." },
  { label: "Show products rated at least 4.5 stars.", text: "Show products rated at least 4.5 stars." },
  { label: "Recommend healthy snacks under $10.", text: "Recommend healthy snacks under $10." },
  { label: "Compare two products.", text: "Compare organic almonds and roasted cashews." },
  { label: "Find a product similar to my uploaded image.", image: true },
];

export default function ChatPage() {
  const { messages, loading, send, reset } = useChat();
  const [draft, setDraft] = useState("");
  const bottomRef = useRef(null);
  const navigate = useNavigate();
  const location = useLocation();
  const handedOver = useRef(false);

  // The image-search page can hand an uploaded image to the assistant.
  useEffect(() => {
    const imageId = location.state && location.state.imageId;
    if (imageId && !handedOver.current) {
      handedOver.current = true;
      navigate(".", { replace: true, state: null });
      send("Find products similar to the image I uploaded.", imageId);
    }
  }, [location.state, navigate, send]);

  useEffect(() => {
    if (bottomRef.current) bottomRef.current.scrollIntoView({ block: "end" });
  }, [messages, loading]);

  function submit(event) {
    event.preventDefault();
    if (!draft.trim() || loading) return;
    send(draft);
    setDraft("");
  }

  function onKeyDown(event) {
    if (event.key === "Enter" && !event.shiftKey) submit(event);
  }

  function pickSuggestion(suggestion) {
    if (suggestion.image) navigate("/image-search");
    else send(suggestion.text);
  }

  return (
    <div className="mx-auto flex max-w-4xl flex-col">
      <div className="flex items-start justify-between gap-3">
        <div>
          <h1 className="text-3xl font-bold">What are you shopping for?</h1>
          <p className="mt-1 max-w-xl text-ink/70">
            Ask in your own words. Prices, ratings and reviews come straight from the store database, and nothing is
            ordered until you confirm at checkout.
          </p>
        </div>
        {messages.length > 0 && (
          <button type="button" className="btn-secondary shrink-0" onClick={reset}>
            <RotateCcw size={16} aria-hidden="true" /> New chat
          </button>
        )}
      </div>

      <div className="mt-6 space-y-4" role="log" aria-live="polite" aria-label="Conversation">
        {messages.length === 0 && (
          <div className="card p-5">
            <p className="flex items-center gap-2 font-semibold">
              <Leaf size={18} className="text-leaf" aria-hidden="true" />
              Hi! I can search the catalog, compare products and recommend the best rated ones. Try one of these:
            </p>
            <div className="mt-4 flex flex-wrap gap-2">
              {SUGGESTIONS.map((s) => (
                <button
                  key={s.label}
                  type="button"
                  className="btn-secondary text-left"
                  onClick={() => pickSuggestion(s)}
                  disabled={loading}
                >
                  {s.image && <Camera size={16} aria-hidden="true" />}
                  {s.label}
                </button>
              ))}
            </div>
          </div>
        )}

        {messages.map((m) => (
          <ChatMessage key={m.id} message={m} />
        ))}

        {loading && (
          <div className="flex items-center gap-2 text-ink/70" role="status">
            <Leaf size={18} className="text-leaf" aria-hidden="true" />
            <span>Checking the catalog</span>
            <span aria-hidden="true" className="flex gap-1">
              {[0, 1, 2].map((i) => (
                <span key={i} className="typing-dot h-1.5 w-1.5 rounded-full bg-leaf" style={{ animationDelay: `${i * 0.2}s` }} />
              ))}
            </span>
          </div>
        )}
        <div ref={bottomRef} />
      </div>

      <form onSubmit={submit} className="sticky bottom-0 mt-6 border-t border-mist bg-paper py-3">
        <label htmlFor="chat-input" className="sr-only">Message the shopping assistant</label>
        <div className="flex items-end gap-2">
          <textarea
            id="chat-input"
            rows={1}
            maxLength={1000}
            value={draft}
            onChange={(e) => setDraft(e.target.value)}
            onKeyDown={onKeyDown}
            placeholder="e.g. organic honey under $20 with 4.5+ rating"
            className="input max-h-40 min-h-[2.75rem] flex-1 resize-y"
          />
          <button type="submit" className="btn-primary h-11" disabled={loading || !draft.trim()}>
            <Send size={16} aria-hidden="true" /> Send
          </button>
        </div>
        <p className="mt-1 text-xs text-ink/60">Enter to send, Shift+Enter for a new line.</p>
      </form>
    </div>
  );
}
