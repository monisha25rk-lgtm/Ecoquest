import { apiRequest } from "./api.js";

export const notificationService = {
  list: (params = {}) => {
    const query = new URLSearchParams();
    Object.entries(params).forEach(([key, value]) => query.set(key, String(value)));
    return apiRequest(`/notifications${query.size ? `?${query}` : ""}`);
  },
  unreadCount: () => apiRequest("/notifications/unread-count"),
  markRead: (id) => apiRequest(`/notifications/${id}/read`, { method: "PATCH" }),
  markAllRead: () => apiRequest("/notifications/read-all", { method: "PATCH" }),
};
