import { apiFetch } from "./client";

export const listPlants = (filters = {}) => {
  const params = new URLSearchParams(Object.entries(filters).filter(([, v]) => v));
  const qs = params.toString();
  return apiFetch(`/api/plants${qs ? `?${qs}` : ""}`);
};

export const getPlant = (id) => apiFetch(`/api/plants/${id}`);

export const createPlant = (data) =>
  apiFetch("/api/plants", { method: "POST", body: JSON.stringify(data) });

export const updatePlant = (id, data) =>
  apiFetch(`/api/plants/${id}`, { method: "PATCH", body: JSON.stringify(data) });

export const deletePlant = (id) => apiFetch(`/api/plants/${id}`, { method: "DELETE" });
