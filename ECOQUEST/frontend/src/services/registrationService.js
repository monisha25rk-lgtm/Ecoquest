import { apiRequest } from "./api.js";

export const registrationService = {
  register: (eventId) => apiRequest(`/events/${eventId}/register`, { method: "POST" }),
  mine: () => apiRequest("/registrations/me"),
};
