/**
 * Backend API base URL. Swapped per environment at build time once the backend
 * (Phase 5) exists and an env-driven build config is introduced.
 */
export const API_BASE_URL = "http://localhost:8000/api/v1";

export const API_ENDPOINTS = {
  optimize: `${API_BASE_URL}/optimize`,
  analyze: `${API_BASE_URL}/analyze`,
  estimateTokens: `${API_BASE_URL}/estimate-tokens`,
  validate: `${API_BASE_URL}/validate`,
  providers: `${API_BASE_URL}/providers`,
  models: `${API_BASE_URL}/models`,
  usage: `${API_BASE_URL}/usage`,
  settings: `${API_BASE_URL}/settings`,
  feedback: `${API_BASE_URL}/feedback`,
} as const;
