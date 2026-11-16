import { apiRequest } from "./api.js";

const endpoints = {
  summary: import.meta.env.VITE_GAMIFICATION_SUMMARY_URL,
  badges: import.meta.env.VITE_GAMIFICATION_BADGES_URL,
  leaderboard: import.meta.env.VITE_GAMIFICATION_LEADERBOARD_URL,
};

async function getConfigured(endpoint, resource) {
  if (!endpoint) return { available: false, reason: `${resource} API has not been configured by Person 3 yet.` };
  const result = await apiRequest(endpoint);
  return { available: true, data: result };
}

export const gamificationService = {
  summary: () => getConfigured(endpoints.summary, "Eco Points"),
  badges: () => getConfigured(endpoints.badges, "Badges"),
  leaderboard: () => getConfigured(endpoints.leaderboard, "Leaderboard"),
};
