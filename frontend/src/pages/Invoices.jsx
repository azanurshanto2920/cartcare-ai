import { useCallback, useEffect, useRef, useState } from "react";
import { Link, useNavigate } from "react-router-dom";

import { clearToken, getInvoice, getInvoices, getMe, uploadInvoice } from "../api.js";
import "./Admin.css";
import "./Knowledge.css";
import "./Invoices.css";

const TABS = [
  { key: "all", label: "All" },
  { key: "review", label: "Needs review" },
];

function money(value, currency = "USD") {
  if (value === null || value === undefined) return "—";
  try {
    return new Intl.NumberFormat("en-US", { style: "currency", currency }).format(value);
  } catch {
    return String(value);
  }
}

export default function Invoices() {
  const navigate = useNavigate();
  const fileRef = useRef(null);
  const [allowed, setAllowed] = useState(null);
  const [invoices, setInvoices] = useState([]);
  const [tab, setTab] = useState("all");
  const [expanded, setExpanded] = useState(null);
  const [details, setDetails] = useState({});
  const [file, setFile] = useState(null);
  const [loading, setLoading] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [notice, setNotice] = useState("");
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

  const loadInvoices = useCallback(() => {
    setLoading(true);
    getInvoices()
      .then(setInvoices)
      .catch(handleError)
      .finally(() => setLoading(false));
  }, [handleError]);

  useEffect(() => {
    if (allowed) loadInvoices();
  }, [allowed, loadInvoices]);

  async function handleUpload(event) {
    event.preventDefault();
    if (!file) return;

    setError("");
    setNotice("");
    setUploading(true);
    try {
      const result = await uploadInvoice(file);
      setNotice(
        result.needs_review
          ? `${result.filename} was read, but it needs review.`
          : `${result.filename} was read and passed all checks.`
      );
      setDetails((current) => ({ ...current, [result.id]: result }));
      setExpanded(result.id);
      setTab("all");
      setFile(null);
      if (fileRef.current) fileRef.current.value = "";
      loadInvoices();
    } catch (err) {
      handleError(err);
    } finally {
      setUploading(false);
    }
  }

  async function toggle(id) {
    if (expanded === id) {
      setExpanded(null);
      return;
    }
    setExpanded(id);
    if (details[id]) return;
    try {
      const result = await getInvoice(id);
      setDetails((current) => ({ ...current, [id]: result }));
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
          <p>This account cannot view invoices.</p>
          <Link to="/" className="btn btn-quiet">
            Back to chat
          </Link>
        </div>
      </main>
    );
  }

  const visible = tab === "review" ? invoices.filter((i) => i.needs_review) : invoices;

  return (
    <div className="admin">
      <header className="admin-head">
        <div className="admin-head-left">
          <span className="brand">CartCare</span>
          <h1>Invoices</h1>
        </div>
        <div className="ticket-actions">
          <Link to="/admin" className="btn btn-quiet btn-small">
            Tickets
          </Link>
          <Link to="/admin/knowledge" className="btn btn-quiet btn-small">
            Knowledge base
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
        <p className="knowledge-intro">
          Upload a supplier invoice and the assistant reads its details. The totals are checked again
          automatically, and anything that does not add up is flagged for review.
        </p>

        <form className="upload" onSubmit={handleUpload}>
          <input
            ref={fileRef}
            type="file"
            accept=".pdf"
            className="upload-file"
            aria-label="Choose an invoice"
            onChange={(e) => setFile(e.target.files?.[0] ?? null)}
          />
          <button type="submit" className="btn btn-primary" disabled={!file || uploading}>
            {uploading ? "Reading…" : "Upload"}
          </button>
          <p className="upload-note">
            PDF only, up to 10 MB. Reading an invoice takes a few seconds. Scanned PDFs without selectable
            text are not supported.
          </p>
        </form>

        {notice && (
          <p className="notice" role="status">
            {notice}
          </p>
        )}
        {error && (
          <p className="error-text" role="alert">
            {error}
          </p>
        )}

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

        <div className="invoices">
          {loading && <p className="admin-note">Loading invoices…</p>}

          {!loading && visible.length === 0 && (
            <p className="admin-note">
              {tab === "review" ? "Nothing needs review." : "No invoices yet. Upload one to get started."}
            </p>
          )}

          {!loading &&
            visible.map((inv) => {
              const isExpanded = expanded === inv.id;
              const detail = details[inv.id];
              return (
                <article key={inv.id} className="invoice">
                  <div className="invoice-row">
                    <div className="invoice-main">
                      <span className="invoice-title">{inv.vendor || inv.filename}</span>
                      <span className="invoice-meta">
                        {inv.invoice_number ? `${inv.invoice_number} · ` : ""}
                        {inv.invoice_date || "No date"} · {inv.filename}
                      </span>
                    </div>
                    <span className="invoice-total num">{money(inv.total)}</span>
                    <span className={`review-state ${inv.needs_review ? "needs-review" : ""}`}>
                      <span className="status-dot" aria-hidden="true" />
                      {inv.needs_review ? "Needs review" : "Checks passed"}
                    </span>
                    <button
                      type="button"
                      className="btn btn-quiet btn-small"
                      aria-expanded={isExpanded}
                      onClick={() => toggle(inv.id)}
                    >
                      {isExpanded ? "Hide details" : "View details"}
                    </button>
                  </div>

                  {isExpanded && (
                    <div className="invoice-detail">
                      {!detail && <p className="admin-note">Loading details…</p>}

                      {detail && detail.warnings.length > 0 && (
                        <div className="warning-box" role="note">
                          {detail.warnings.map((w) => (
                            <p key={w}>{w}</p>
                          ))}
                        </div>
                      )}

                      {detail && (
                        <div className="table-scroll">
                          <table className="items-table">
                            <thead>
                              <tr>
                                <th>Description</th>
                                <th>Qty</th>
                                <th>Unit price</th>
                                <th>Amount</th>
                              </tr>
                            </thead>
                            <tbody>
                              {detail.invoice.items.map((item, index) => (
                                <tr key={`${item.description}-${index}`}>
                                  <td>{item.description}</td>
                                  <td className="num">{item.quantity}</td>
                                  <td className="num">{money(item.unit_price, detail.invoice.currency)}</td>
                                  <td className="num">
                                    {money(item.line_total ?? item.quantity * item.unit_price, detail.invoice.currency)}
                                  </td>
                                </tr>
                              ))}
                            </tbody>
                            <tfoot>
                              <tr>
                                <td colSpan={3}>Subtotal</td>
                                <td className="num">{money(detail.invoice.subtotal, detail.invoice.currency)}</td>
                              </tr>
                              {detail.invoice.adjustments.map((a, index) => (
                                <tr key={`${a.label}-${index}`}>
                                  <td colSpan={3}>{a.label}</td>
                                  <td className="num">{money(a.amount, detail.invoice.currency)}</td>
                                </tr>
                              ))}
                              <tr className="grand">
                                <td colSpan={3}>Total</td>
                                <td className="num">{money(detail.invoice.total, detail.invoice.currency)}</td>
                              </tr>
                            </tfoot>
                          </table>
                        </div>
                      )}
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