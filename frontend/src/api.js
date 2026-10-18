const BASE_URL = import.meta.env.VITE_API_URL || "http://127.0.0.1:8000";
const TOKEN_KEY = "cartcare_token";

export class ApiError extends Error {
  constructor(message, status) {
    super(message);
    this.status = status;
  }
}

export function getToken() {
  try {
    return localStorage.getItem(TOKEN_KEY);
  } catch {
    return null;
  }
}

function setToken(token) {
  try {
    localStorage.setItem(TOKEN_KEY, token);
  } catch {
    // Storage can be blocked; the session just will not persist
  }
}

export function clearToken() {
  try {
    localStorage.removeItem(TOKEN_KEY);
  } catch {
    // Nothing to clear
  }
}

async function request(path, { method = "GET", body, isForm = false } = {}) {
  const headers = {};
  const token = getToken();
  if (token) headers.Authorization = `Bearer ${token}`;
  if (body && !isForm) headers["Content-Type"] = "application/json";

  let response;
  try {
    response = await fetch(`${BASE_URL}${path}`, {
      method,
      headers,
      body: body ? (isForm ? body : JSON.stringify(body)) : undefined,
    });
  } catch {
    throw new ApiError("Cannot reach the server. Check your connection and try again.", 0);
  }

  let data = null;
  try {
    data = await response.json();
  } catch {
    // Response had no JSON body
  }

  if (response.status === 401) clearToken();

  if (!response.ok) {
    const detail = typeof data?.detail === "string" ? data.detail : "Something went wrong.";
    throw new ApiError(detail, response.status);
  }
  return data;
}

export async function login(username, password) {
  const data = await request("/login", { method: "POST", body: { username, password } });
  if (data.error) throw new ApiError(data.error, 401);
  setToken(data.access_token);
}

export async function register(username, password) {
  const data = await request("/register", { method: "POST", body: { username, password } });
  if (data.error) throw new ApiError(data.error, 400);
}

export function getMe() {
  return request("/me");
}

export function sendMessage(message) {
  return request("/chat", { method: "POST", body: { message } });
}

export function getHistory() {
  return request("/history");
}

export function getDocuments() {
  return request("/admin/documents");
}

export function uploadDocument(file) {
  const form = new FormData();
  form.append("file", file);
  return request("/admin/documents", { method: "POST", body: form, isForm: true });
}

export function deleteDocument(source) {
  return request(`/admin/documents/${encodeURIComponent(source)}`, { method: "DELETE" });
}

export function getTickets(status) {
  const query = status ? `?status=${encodeURIComponent(status)}` : "";
  return request(`/admin/tickets${query}`);
}

export function updateTicket(id, status) {
  return request(`/admin/tickets/${id}`, { method: "PATCH", body: { status } });
}


export function getInvoices() {
  return request("/admin/invoices");
}

export function getInvoice(id) {
  return request(`/admin/invoices/${id}`);
}

export function uploadInvoice(file) {
  const form = new FormData();
  form.append("file", file);
  return request("/admin/invoices", { method: "POST", body: form, isForm: true });
}