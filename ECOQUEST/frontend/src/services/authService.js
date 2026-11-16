import { apiRequest } from "./api.js";

export const authService = {
  register: (values) => apiRequest("/auth/register", { method: "POST", body: JSON.stringify(values) }),
  login: (email, password) => apiRequest("/auth/login", { method: "POST", body: JSON.stringify({ email, password }) }),
  me: () => apiRequest("/auth/me"),
};
