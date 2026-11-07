import { useCallback, useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";

import { clearToken, getAnalytics, getMe } from "../api.js";
import "./Admin.css";
import "./Analytics.css";

function seconds(ms) {
  return `${(ms / 1000).toFixed(1)} s`;
}

function formatDate(value) {
  // The API sends UTC times without a timezone marker
  const date = new Date(value.endsWith("Z") ? value : `${value}Z`);
  return date.toLocaleString(undefined, { dateStyle: "medium", timeStyle: "short" });
}

function weekday(isoDate) {
  return new Date(`${isoDate}T00:00:00Z`).toLocaleDateString(undefined, {
    weekday: "short",
    timeZone: "UTC",
  });
}

function Row({ name, value }) {
  return (
    <div className="stat-row">
      <span className="stat-name">{name}</span>
      <span className="stat-value num">{value}</span>
    </div>
  );
}

export default function Analytics() {
  const navigate = useNavigate();
  const [allowed, setAllowed] = useState(null);
  const [data, setData] = useState(null);
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

  const load = useCallback(() => {
    setLoading(true);
    setError("");
    getAnalytics()
      .then(setData)
      .catch(handleError)
      .finally(() => setLoading(false));
  }, [handleError]);

  useEffect(() => {
    if (allowed) load();
  }, [allowed, load]);

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
          <p>This account cannot view analytics.</p>
          <Link to="/" className="btn btn-quiet">
            Back to chat
          </Link>
        </div>
      </main>
    );
  }

  const maxChats = data ? Math.max(1, ...data.daily.map((d) => d.chats)) : 1;

  return (
    <div className="admin">
      <header className="admin-head">
        <div className="admin-head-left">
          <span className="brand">CartCare</span>
          <h1>Analytics</h1>
        </div>
        <div className="ticket-actions">
          <Link to="/admin" className="btn btn-quiet btn-small">
            Tickets
          </Link>
          <Link to="/admin/knowledge" className="btn btn-quiet btn-small">
            Knowledge base
          </Link>
          <Link to="/admin/invoices" className="btn btn-quiet btn-small">
            Invoices
          </Link>
          <Link to="/" className="btn btn-quiet btn-small">
            Back to chat
          </Link>
          <button type="button" className="btn btn-quiet btn-small" onClick={signOut}>
            Sign out
          </button>
        </div>
      </header>

      <main className="admin-body">
        {error && (
          <p className="error-text" role="alert">
            {error}
          </p>
        )}
        {loading && !data && <p className="admin-note">Loading analytics…</p>}

        {data && (
          <>
            <h2 className="section-title">Questions that need attention</h2>
            <div className="panel attention">
              {data.needs_attention.length === 0 && (
                <p className="admin-note">
                  Nothing to review. Questions the assistant could not answer will appear here.
                </p>
              )}
              {data.needs_attention.map((item) => (
                <div key={item.id} className="attention-item">
                  <span className="attention-question">{item.question}</span>
                  <span className="attention-meta">
                    {item.reason} · {formatDate(item.created_at)}
                  </span>
                </div>
              ))}
            </div>

            <h2 className="section-title">At a glance</h2>
            <div className="panel key-figures">
              <div className="key-figure">
                <span className="key-label">Conversations</span>
                <span className="key-value num">{data.chats_total}</span>
                <span className="key-note">{data.chats_last_week} in the last 7 days</span>
              </div>
              <div className="key-figure">
                <span className="key-label">Handed to a human</span>
                <span className="key-value num">{data.handoffs}</span>
                <span className="key-note">
                  {data.handoffs} of {data.chats_total} chats ({data.handoff_rate}%)
                </span>
              </div>
              <div className="key-figure">
                <span className="key-label">Typical response time</span>
                <span className="key-value num">{seconds(data.median_ms)}</span>
                <span className="key-note">Median of all replies</span>
              </div>
            </div>

            <h2 className="section-title">Chats per day</h2>
            <div className="panel">
              <div className="bars" role="img" aria-label="Chats per day over the last 7 days">
                {data.daily.map((day) => (
                  <div key={day.date} className="bar-column">
                    <div className="bar-track">
                      <span className="bar-count num">{day.chats}</span>
                      <div className="bar" style={{ height: `${Math.round((day.chats / maxChats) * 80)}%` }} />
                    </div>
                    <span className="bar-day">{weekday(day.date)}</span>
                  </div>
                ))}
              </div>
            </div>

            <div className="split">
              <div>
                <h2 className="section-title">Response time</h2>
                <div className="panel">
                  <Row name="Average" value={seconds(data.average_ms)} />
                  <Row name="Median" value={seconds(data.median_ms)} />
                  <Row name="Slowest" value={seconds(data.slowest_ms)} />
                  <Row name="Failed replies" value={`${data.failed} (${data.failure_rate}%)`} />
                </div>
              </div>

              <div>
                <h2 className="section-title">Tools used</h2>
                <div className="panel">
                  {data.tools.length === 0 && <p className="admin-note">No tools used yet.</p>}
                  {data.tools.map((tool) => (
                    <Row key={tool.name} name={tool.name} value={tool.count} />
                  ))}
                </div>
              </div>
            </div>

            <div className="split">
              <div>
                <h2 className="section-title">Support tickets</h2>
                <div className="panel">
                  <Row name="Open" value={data.tickets.open} />
                  <Row name="Resolved" value={data.tickets.resolved} />
                </div>
              </div>

              <div>
                <h2 className="section-title">Invoices</h2>
                <div className="panel">
                  <Row name="Processed" value={data.invoices.total} />
                  <Row name="Needs review" value={data.invoices.needs_review} />
                </div>
              </div>
            </div>
          </>
        )}
      </main>
    </div>
  );
}