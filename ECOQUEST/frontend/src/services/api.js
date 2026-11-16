const API_BASE_URL = (import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000").replace(/\/+$/, "");
const TOKEN_KEY = "ecoquest.accessToken";

export class ApiError extends Error {
  constructor(message, status, detail) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.detail = detail;
  }
}

export function getToken() {
  return window.localStorage.getItem(TOKEN_KEY) || window.sessionStorage.getItem(TOKEN_KEY);
}

export function setToken(token, remember = true) {
  clearToken();
  const storage = remember ? window.localStorage : window.sessionStorage;
  storage.setItem(TOKEN_KEY, token);
}

export function clearToken() {
  window.localStorage.removeItem(TOKEN_KEY);
  window.sessionStorage.removeItem(TOKEN_KEY);
}

export async function apiRequest(path, options = {}) {
  const headers = new Headers(options.headers || {});
  const token = getToken();
  if (token) headers.set("Authorization", `Bearer ${token}`);
  if (options.body !== undefined && !(options.body instanceof FormData)) headers.set("Content-Type", "application/json");
  let response;
  try {
    const url = /^https?:\/\//i.test(path) ? path : `${API_BASE_URL}${path}`;
    response = await fetch(url, { ...options, headers });
  } catch (error) {
    throw new ApiError("Could not reach EcoQuest. Check that the backend is running.", 0, error);
  }
  const contentType = response.headers.get("content-type") || "";
  const body = contentType.includes("application/json") ? await response.json() : await response.text();
  if (!response.ok) {
    if (response.status === 401) {
      clearToken();
      window.dispatchEvent(new Event("ecoquest:unauthorized"));
    }
    const detail = body && typeof body === "object" ? body.detail : body;
    const message = Array.isArray(detail) ? detail.map((item) => item.msg).join(", ") : (detail || `Request failed (${response.status}).`);
    throw new ApiError(message, response.status, detail);
  }
  return body;
}

export const apiUrl = API_BASE_URL;
