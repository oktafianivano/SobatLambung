
import { API_URL } from '../config';

export const API_PREFIX = '/api/v1';

export function apiUrl(path: string): string {
  const normalized = path.startsWith('/') ? path : `/${path}`;
  return `${API_URL}${API_PREFIX}${normalized}`;
}

/**
 * Header JSON standar.
 * Autentikasi menggunakan HttpOnly Cookie melalui credentials: include.
 */
export function jsonHeaders(): Record<string, string> {
  return {
    'Content-Type': 'application/json',
  };
}
