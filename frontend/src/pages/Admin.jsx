import { useCallback, useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";

import { clearToken, getMe, getTickets, updateTicket } from "../api.js";
import "./Admin.css";

const TABS = [
  { key: "open", label: "Open" },
  { key: "resolved", label: "Resolved" },
  { key: "all", label: "All" },
];

function formatDate(value) {
  // The API sends UTC times without a timezone marker
  const date = new Date(value.endsWith("Z") ? value : `${value}Z`);
  return date.toLocaleString(undefined, { dateStyle: "medium", timeStyle: "short" });
}

export default function Admin() {
  const navigate = useNavigate();
  const [allowed, setAllowed] = useState(null);
  const [tab, setTab] = useState("open");
  const [tickets, setTickets] = useState([]);
  const [expanded, setExpanded] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  function signOut() {
    clearToken();
    navigate("/login");
  }

  const handleError = useCallback(
    (err) => {
      if (err.status === 401) {
        navigate("/login");
        return;
      }
      setError(err.message);
    },
    [navigate]
  );

  // Check that the signed-in user is an admin
  useEffect(() => {
    getMe()
      .then((me) => setAllowed(me.is_admin))
      .catch(handleError);
  }, [handleError]);

  const loadTickets = useCallback(() => {
    setLoading(true);
    setError("");
    getTickets(tab === "all" ? undefined : tab)
      .then(setTickets)
      .catch(handleError)
      .finally(() => setLoading(false));
  }, [tab, handleError]);

  useEffect(() => {
    if (allowed) loadTickets();
  }, [allowed, loadTickets]);

  async function changeStatus(ticket, status) {
    setError("");
    try {
      await updateTicket(ticket.id, status);
      loadTickets();
    } catch (err) {
      handleError(err);
    }
  }

  if (allowed === null) {
    return (
      <main className="auth-page">
        <p className="admin-note">{error || "Loading…"}</p>
      </main>
    );
  }

  if (allowed === false) {
    return (
      <main className="auth-page">
        <div style={{ display: "grid", gap: 12, justifyItems: "start" }}>
          <h1>Admin access required</h1>
          <p>This account cannot view support tickets.</p>
          <Link to="/" className="btn btn-quiet">
            Back to chat
          </Link>
        </div>
      </main>
    );
  }

  return (
    <div className="admin">
      <header className="admin-head">
        <div className="admin-head-left">
          <span className="brand">CartCare</span>
          <h1>Support tickets</h1>
        </div>
        <div className="ticket-actions">
          <Link to="/" className="btn btn-quiet btn-small">
            Back to chat
          </Link>
          <button type="button" className="btn btn-quiet btn-small" onClick={signOut}>
            Sign out
          </button>
        </div>
      </header>

      <main className="admin-body">
        <div className="tabs" role="tablist">
          {TABS.map((t) => (
            <button
              key={t.key}
              type="button"
              role="tab"
              className="tab"
              aria-selected={tab === t.key}
              onClick={() => setTab(t.key)}
            >
              {t.label}
            </button>
          ))}
        </div>

        {error && (
          <p className="error-text" role="alert">
            {error}
          </p>
        )}

        <div className="tickets">
          {loading && <p className="admin-note">Loading tickets…</p>}

          {!loading && tickets.length === 0 && (
            <p className="admin-note">
              {tab === "open" ? "No open tickets. New requests for a human agent will appear here." : "No tickets here."}
            </p>
          )}

          {!loading &&
            tickets.map((ticket) => {
              const isOpen = ticket.status === "open";
              const isExpanded = expanded === ticket.id;
              return (
                <article key={ticket.id} className="ticket">
                  <div className="ticket-row">
                    <span className="ticket-id num">#{ticket.id}</span>
                    <div className="ticket-reason">
                      {ticket.reason}
                      <span className="ticket-meta">
                        User {ticket.user_id} · {formatDate(ticket.created_at)}
                      </span>
                    </div>
                    <span className={`ticket-status ${isOpen ? "is-open" : ""}`}>
                      <span className="status-dot" aria-hidden="true" />
                      {isOpen ? "Open" : "Resolved"}
                    </span>
                    <div className="ticket-actions">
                      <button
                        type="button"
                        className="btn btn-quiet btn-small"
                        aria-expanded={isExpanded}
                        onClick={() => setExpanded(isExpanded ? null : ticket.id)}
                      >
                        {isExpanded ? "Hide chat" : "View chat"}
                      </button>
                      <button
                        type="button"
                        className={`btn btn-small ${isOpen ? "btn-primary" : "btn-quiet"}`}
                        onClick={() => changeStatus(ticket, isOpen ? "resolved" : "open")}
                      >
                        {isOpen ? "Mark resolved" : "Reopen"}
                      </button>
                    </div>
                  </div>

                  {isExpanded && (
                    <div className="ticket-detail">
                      <div className="transcript">{ticket.conversation}</div>
                    </div>
                  )}
                </article>
              );
            })}
        </div>
      </main>
    </div>
  );
}