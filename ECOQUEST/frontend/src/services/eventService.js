import { apiRequest } from "./api.js";

export const eventService = {
  list: (filters = {}) => {
    const params = new URLSearchParams();
    Object.entries(filters).forEach(([key, value]) => {
      if (value !== "" && value !== null && value !== undefined && value !== false) params.set(key, String(value));
    });
    return apiRequest(`/events${params.size ? `?${params}` : ""}`);
  },
  get: (eventId) => apiRequest(`/events/${eventId}`),
};
