import { Navigate, Route, Routes, useNavigate } from "react-router-dom";

import { clearToken, getToken } from "./api.js";
import Auth from "./pages/Auth.jsx";

function RequireAuth({ children }) {
  return getToken() ? children : <Navigate to="/login" replace />;
}

// Temporary page, replaced by the real chat page in a later step
function Home() {
  const navigate = useNavigate();

  function signOut() {
    clearToken();
    navigate("/login");
  }

  return (
    <main className="auth-page">
      <div style={{ display: "grid", gap: 12, justifyItems: "start" }}>
        <h1>You are signed in</h1>
        <p>The chat page comes next.</p>
        <button type="button" className="btn btn-quiet" onClick={signOut}>
          Sign out
        </button>
      </div>
    </main>
  );
}

export default function App() {
  return (
    <Routes>
      <Route path="/login" element={<Auth />} />
      <Route
        path="/"
        element={
          <RequireAuth>
            <Home />
          </RequireAuth>
        }
      />
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}