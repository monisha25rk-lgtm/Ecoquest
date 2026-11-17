import { apiRequest } from "./api.js";

export const pointsService = {
  summary: () => apiRequest("/points/me"),
};
