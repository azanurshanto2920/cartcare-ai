import { Navigate, Route, Routes } from "react-router-dom";

import { getToken } from "./api.js";
import Admin from "./pages/Admin.jsx";
import Auth from "./pages/Auth.jsx";
import Chat from "./pages/Chat.jsx";
import Invoices from "./pages/Invoices.jsx";
import Knowledge from "./pages/Knowledge.jsx";

function RequireAuth({ children }) {
  return getToken() ? children : <Navigate to="/login" replace />;
}

export default function App() {
  return (
    <Routes>
      <Route path="/login" element={<Auth />} />
      <Route
        path="/"
        element={
          <RequireAuth>
            <Chat />
          </RequireAuth>
        }
      />
      <Route
        path="/admin"
        element={
          <RequireAuth>
            <Admin />
          </RequireAuth>
        }
      />
      <Route
        path="/admin/knowledge"
        element={
          <RequireAuth>
            <Knowledge />
          </RequireAuth>
        }
      />
      <Route
        path="/admin/invoices"
        element={
          <RequireAuth>
            <Invoices />
          </RequireAuth>
        }
      />
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}