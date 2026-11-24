/**
 * Konfigurasi frontend.
 *
 * Urutan prioritas:
 * 1. `VITE_API_URL` dari file `.env` / build arg (dipakai saat deploy/Docker).
 * 2. Fallback lokal: `http://<host-halaman>:8000` (dev/LAN).
 * 3. Fallback produksi: origin yang sama (reverse proxy `/api` -> backend).
 *
 * Fallback produksi sengaja memakai origin yang sama agar cookie
 * autentikasi tetap first-party dan tidak diblokir browser.
 */
const isBrowser = typeof window !== 'undefined';
const pageHost = isBrowser ? window.location.hostname : 'localhost';

const isLocalHost =
  pageHost === 'localhost' ||
  pageHost === '127.0.0.1' ||
  pageHost === '0.0.0.0' ||
  pageHost === '[::1]' ||
  /^10\.\d{1,3}\.\d{1,3}\.\d{1,3}$/.test(pageHost) ||
  /^192\.168\.\d{1,3}\.\d{1,3}$/.test(pageHost) ||
  /^172\.(1[6-9]|2\d|3[0-1])\.\d{1,3}\.\d{1,3}$/.test(pageHost);

const fallbackBaseUrl = isLocalHost ? `http://${pageHost}:8000` : '';

const envBaseUrl = import.meta.env.VITE_API_URL?.trim();

export const API_URL = (envBaseUrl || fallbackBaseUrl).replace(/\/+$/, '');
