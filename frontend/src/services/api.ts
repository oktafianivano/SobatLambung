/**
 * Satu pintu untuk seluruh pemanggilan HTTP ke backend.
 *
 * Semua komponen WAJIB memakai `apiUrl()` agar versi API hanya diubah di
 * satu tempat (saat ini `/api/v1`). Backend tetap menyediakan alias `/api`
 * untuk kompatibilitas, tetapi frontend selalu memakai versi terbaru.
 */

import { API_URL } from '../config';

export const API_PREFIX = '/api/v1';

/** Bangun URL absolut menuju endpoint backend, mis. apiUrl('/user/profile'). */
export function apiUrl(path: string): string {
  const normalized = path.startsWith('/') ? path : `/${path}`;
  return `${API_URL}${API_PREFIX}${normalized}`;
}

/** Header JSON standar, opsional dengan Bearer token. */
export function jsonHeaders(token?: string | null): Record<string, string> {
  const headers: Record<string, string> = { 'Content-Type': 'application/json' };
  if (token) headers.Authorization = `Bearer ${token}`;
  return headers;
}
