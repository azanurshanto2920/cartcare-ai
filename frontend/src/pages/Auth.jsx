import { useState } from "react";
import { useNavigate } from "react-router-dom";

import { login, register } from "../api.js";
import "./Auth.css";

export default function Auth() {
  const navigate = useNavigate();
  const [mode, setMode] = useState("login");
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  const isLogin = mode === "login";

  async function handleSubmit(event) {
    event.preventDefault();
    setError("");
    setBusy(true);
    try {
      if (!isLogin) await register(username, password);
      await login(username, password);
      navigate("/");
    } catch (err) {
      setError(err.message);
    } finally {
      setBusy(false);
    }
  }

  function switchMode() {
    setMode(isLogin ? "register" : "login");
    setError("");
  }

  return (
    <main className="auth-page">
      <form className="plate" onSubmit={handleSubmit}>
        <div className="plate-head">
          <span className="brand">CartCare</span>
          <span className="status">
            <span className="status-dot" aria-hidden="true" />
            Assistant available
          </span>
        </div>

        <p className="plate-intro">
          {isLogin
            ? "Sign in to ask about products, track an order or reach a support agent."
            : "Create an account to start a conversation with our support assistant."}
        </p>

        <div className="plate-row">
          <label htmlFor="username">Username</label>
          <input
            id="username"
            className="input"
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            autoComplete="username"
            required
          />
        </div>

        <div className="plate-row">
          <label htmlFor="password">Password</label>
          <input
            id="password"
            type="password"
            className="input"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            autoComplete={isLogin ? "current-password" : "new-password"}
            required
          />
        </div>

        <div className="plate-actions">
          {error && (
            <p className="error-text" role="alert">
              {error}
            </p>
          )}
          <button type="submit" className="btn btn-primary" disabled={busy}>
            {busy ? "Please wait…" : isLogin ? "Sign in" : "Create account"}
          </button>
        </div>

        <p className="plate-foot">
          {isLogin ? "New here? " : "Already have an account? "}
          <button type="button" className="link-button" onClick={switchMode}>
            {isLogin ? "Create an account" : "Sign in"}
          </button>
        </p>
      </form>
    </main>
  );
}