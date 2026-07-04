import { apiFetch } from "./client";

export const getStats = () => apiFetch("/api/stats");
