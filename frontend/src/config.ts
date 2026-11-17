// Backend base URL.
// - Default: ikut host yang sedang membuka frontend (localhost, IP LAN, dsb.)
// - Bisa dioverride lewat env VITE_API_URL saat build/dev.
const envUrl = import.meta.env.VITE_API_URL?.trim();

export const API_URL = (
  envUrl && envUrl.length > 0 ? envUrl : `http://${window.location.hostname}:8000`
).replace(/\/+$/, '');
