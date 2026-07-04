import { apiFetch } from "./client";

export const searchLocalSpecies = (q) =>
  apiFetch(`/api/plant-species/search?q=${encodeURIComponent(q)}`);

export const searchExternalSpecies = (q) =>
  apiFetch(`/api/plant-species/search-external?q=${encodeURIComponent(q)}`, { method: "POST" });
