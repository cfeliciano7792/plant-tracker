import { apiFetch } from "./client";

export const register = (data) =>
  apiFetch("/api/auth/register", { method: "POST", body: JSON.stringify(data) });

export const login = (data) =>
  apiFetch("/api/auth/login", { method: "POST", body: JSON.stringify(data) });

export const logout = () => apiFetch("/api/auth/logout", { method: "POST" });

export const getMe = () => apiFetch("/api/auth/me");
