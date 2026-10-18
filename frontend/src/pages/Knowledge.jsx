import { useCallback, useEffect, useRef, useState } from "react";
import { Link, useNavigate } from "react-router-dom";

import { clearToken, deleteDocument, getDocuments, getMe, uploadDocument } from "../api.js";
import "./Admin.css";
import "./Knowledge.css";

export default function Knowledge() {
  const navigate = useNavigate();
  const fileRef = useRef(null);
  const [allowed, setAllowed] = useState(null);
  const [documents, setDocuments] = useState([]);
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

  const loadDocuments = useCallback(() => {
    setLoading(true);
    getDocuments()
      .then(setDocuments)
      .catch(handleError)
      .finally(() => setLoading(false));
  }, [handleError]);

  useEffect(() => {
    if (allowed) loadDocuments();
  }, [allowed, loadDocuments]);

  async function handleUpload(event) {
    event.preventDefault();
    if (!file) return;

    setError("");
    setNotice("");
    setUploading(true);
    try {
      const result = await uploadDocument(file);
      setNotice(`${result.source} was saved (${result.chunks} sections).`);
      setFile(null);
      if (fileRef.current) fileRef.current.value = "";
      loadDocuments();
    } catch (err) {
      handleError(err);
    } finally {
      setUploading(false);
    }
  }

  async function handleDelete(source) {
    if (!window.confirm(`Remove ${source} from the knowledge base? The assistant will stop using it.`)) {
      return;
    }
    setError("");
    setNotice("");
    try {
      await deleteDocument(source);
      setNotice(`${source} was removed.`);
      loadDocuments();
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
          <p>This account cannot manage the knowledge base.</p>
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
          <h1>Knowledge base</h1>
        </div>
        <div className="ticket-actions">
          <Link to="/admin" className="btn btn-quiet btn-small">
            Tickets
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
          The assistant answers policy questions from the documents below. Upload a file with the same
          name to replace its contents.
        </p>

        <form className="upload" onSubmit={handleUpload}>
          <input
            ref={fileRef}
            type="file"
            accept=".pdf,.txt"
            className="upload-file"
            aria-label="Choose a document"
            onChange={(e) => setFile(e.target.files?.[0] ?? null)}
          />
          <button type="submit" className="btn btn-primary" disabled={!file || uploading}>
            {uploading ? "Uploading…" : "Upload"}
          </button>
          <p className="upload-note">PDF or plain text, up to 10 MB. Scanned PDFs without selectable text are not supported.</p>
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

        <div className="docs">
          {loading && <p className="admin-note">Loading documents…</p>}

          {!loading && documents.length === 0 && (
            <p className="admin-note">No documents yet. Upload your policies and FAQs to get started.</p>
          )}

          {!loading &&
            documents.map((doc) => (
              <div key={doc.source} className="doc-row">
                <span className="doc-name">{doc.source}</span>
                <span className="doc-count num">{doc.chunks} sections</span>
                <button
                  type="button"
                  className="btn btn-small btn-danger"
                  onClick={() => handleDelete(doc.source)}
                >
                  Remove
                </button>
              </div>
            ))}
        </div>
      </main>
    </div>
  );
}