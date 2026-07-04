import { apiFetch } from "./client";

const API_URL = import.meta.env.VITE_API_URL;

export const listPhotos = (plantId) => apiFetch(`/api/plants/${plantId}/photos`);

export const uploadPhoto = (plantId, file) => {
  const formData = new FormData();
  formData.append("file", file);
  return apiFetch(`/api/plants/${plantId}/photos`, { method: "POST", body: formData });
};

export const deletePhoto = (plantId, photoId) =>
  apiFetch(`/api/plants/${plantId}/photos/${photoId}`, { method: "DELETE" });

export const photoUrl = (plantId, photoId) => `${API_URL}/api/plants/${plantId}/photos/${photoId}`;
