import { useEffect, useRef, useState } from "react";
import { Link, useNavigate } from "react-router-dom";

import { clearToken, getHistory, getMe, sendMessage } from "../api.js";
import "./Chat.css";

const SUGGESTIONS = [
  "Which air conditioners do you have under $800?",
  "What is your return policy?",
  "Where is my order? (have your order number and email ready)",
  "I would like to speak with a human agent.",
];

export default function Chat() {
  const navigate = useNavigate();
  const [messages, setMessages] = useState([]);
  const [draft, setDraft] = useState("");
  const [sending, setSending] = useState(false);
  const [loading, setLoading] = useState(true);
  const [isAdmin, setIsAdmin] = useState(false);
  const bottomRef = useRef(null);

  function signOut() {
    clearToken();
    navigate("/login");
  }

  function handleError(err) {
    if (err.status === 401) {
      navigate("/login");
      return;
    }
    setMessages((current) => [
      ...current,
      { id: `error-${Date.now()}`, role: "error", content: err.message },
    ]);
  }

  // Load the previous conversation once (the API returns newest first)
  useEffect(() => {
    getHistory()
      .then((items) => setMessages([...items].reverse()))
      .catch(handleError)
      .finally(() => setLoading(false));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

    // Show the tickets link only to admins
  useEffect(() => {
    getMe()
      .then((me) => setIsAdmin(me.is_admin))
      .catch(() => {});
  }, []);

  // Keep the newest message in view
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ block: "end" });
  }, [messages, sending]);

  async function send(text) {
    const content = text.trim();
    if (!content || sending) return;

    setDraft("");
    setSending(true);
    setMessages((current) => [...current, { id: `local-${Date.now()}`, role: "user", content }]);

    try {
      const data = await sendMessage(content);
      setMessages((current) => [
        ...current,
        { id: `bot-${Date.now()}`, role: "assistant", content: data.reply },
      ]);
    } catch (err) {
      handleError(err);
    } finally {
      setSending(false);
    }
  }

  function handleSubmit(event) {
    event.preventDefault();
    send(draft);
  }

  const showEmpty = !loading && messages.length === 0;

  return (
    <div className="shell">
      <aside className="side">
        <span className="side-brand">CartCare</span>

        <div className="side-section">
          <span className="side-label">What I can help with</span>
          <p className="side-hint">
            Product questions, order tracking, returns, shipping, warranty, and connecting you with a
            support agent.
          </p>
        </div>

        {isAdmin && (
          <nav className="side-nav">
            <Link to="/admin" className="side-link">
              Support tickets
            </Link>
            <Link to="/admin/knowledge" className="side-link">
              Knowledge base
            </Link>
          </nav>
        )}

        <div className="side-bottom">
          <button type="button" className="btn btn-quiet" onClick={signOut}>
            Sign out
          </button>
        </div>
      </aside>

      <section className="convo">
        <header className="convo-head">
          <h1>Support chat</h1>
          <span className="status">
            <span className="status-dot" aria-hidden="true" />
            Assistant available
          </span>
        </header>

        <div className="messages" aria-live="polite">
          {showEmpty && (
            <div className="empty">
              <h2>How can we help?</h2>
              <p className="side-hint">Ask a question, or start with one of these.</p>
              <div className="empty-prompts">
                {SUGGESTIONS.map((text) => (
                  <button key={text} type="button" className="prompt-chip" onClick={() => send(text)}>
                    {text}
                  </button>
                ))}
              </div>
            </div>
          )}

          {messages.map((m) => (
            <div
              key={m.id}
              className={
                m.role === "user"
                  ? "message message-user"
                  : m.role === "error"
                    ? "message message-error"
                    : "message message-bot"
              }
            >
              {m.content}
            </div>
          ))}

          {sending && <p className="typing">Assistant is typing…</p>}
          <div ref={bottomRef} />
        </div>

        <form className="composer" onSubmit={handleSubmit}>
          <input
            className="input"
            value={draft}
            onChange={(e) => setDraft(e.target.value)}
            placeholder="Type your message"
            aria-label="Message"
            disabled={sending}
          />
          <button type="submit" className="btn btn-primary" disabled={sending || !draft.trim()}>
            Send
          </button>
        </form>
      </section>
    </div>
  );
}