/**
 * Konfigurasi frontend.
 *
 * Urutan prioritas:
 * 1. `VITE_API_URL` dari file `.env` / build arg (dipakai saat deploy/Docker).
 * 2. Fallback: host yang sama dengan halaman, port 8000 (nyaman untuk dev LAN).
 */
const fallbackBaseUrl = `http://${window.location.hostname}:8000`;
const envBaseUrl = import.meta.env.VITE_API_URL?.trim();

export const API_URL = (envBaseUrl || fallbackBaseUrl).replace(/\/+$/, '');
