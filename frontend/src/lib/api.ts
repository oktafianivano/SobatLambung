
import { apiUrl } from '../services/api';

const TAB_KEY = 'sobat_lambung_active_tab';

// Kunci lama: dulu token CSRF disimpan di localStorage. Sekarang hanya
// dipakai untuk membersihkan sisa data di browser pengguna.
const LEGACY_CSRF_KEY = 'sobat_lambung_csrf_token';

export const SESSION_UPDATED_EVENT = 'sobatlambung:session-updated';
export const SESSION_EXPIRED_EVENT = 'sobatlambung:session-expired';

const hasStorage = () => {
  if (typeof window === 'undefined') return false;

  try {
    return typeof window.localStorage !== 'undefined';
  } catch {
    return false;
  }
};

// Satu-satunya data yang boleh bertahan di browser adalah state UI
// non-sensitif. Semua key lain (termasuk sisa "session" versi lama yang
// berisi access_token/refresh_token/no_wa) dihapus saat aplikasi dimuat.
const SAFE_STORAGE_KEYS = new Set<string>([TAB_KEY]);

function purgeSensitiveStorage() {
  if (typeof window === 'undefined') return;

  const storages: Storage[] = [];

  try {
    if (window.localStorage) storages.push(window.localStorage);
  } catch {
    // Storage diblokir.
  }

  try {
    if (window.sessionStorage) storages.push(window.sessionStorage);
  } catch {
    // Storage diblokir.
  }

  for (const storage of storages) {
    try {
      const keysToRemove: string[] = [];

      for (let index = 0; index < storage.length; index += 1) {
        const key = storage.key(index);

        if (key && !SAFE_STORAGE_KEYS.has(key)) {
          keysToRemove.push(key);
        }
      }

      keysToRemove.forEach((key) => storage.removeItem(key));
    } catch {
      // Storage bisa diblokir (mode privat / kebijakan browser).
    }
  }
}

purgeSensitiveStorage();

// Token CSRF hanya hidup di memori. Tidak pernah ditulis ke
// localStorage/sessionStorage, sehingga tidak bertahan setelah tab ditutup
// dan tidak bisa dicuri lewat pemeriksaan storage.
let csrfTokenInMemory: string | null = null;

// Bersihkan token CSRF lama yang mungkin masih tersimpan dari versi
// sebelumnya. Access/refresh token sendiri selalu HttpOnly dan tidak pernah
// disentuh JavaScript.
if (hasStorage()) {
  localStorage.removeItem(LEGACY_CSRF_KEY);
}

export function saveActiveTab(tab: string) {
  if (!hasStorage()) return;

  try {
    localStorage.setItem(TAB_KEY, tab);
  } catch {
    // Storage penuh/diblokir: abaikan.
  }
}

export function getSavedActiveTab(): string | null {
  if (!hasStorage()) return null;

  try {
    return localStorage.getItem(TAB_KEY);
  } catch {
    return null;
  }
}

export function storeCsrfToken(token: string | null | undefined) {
  csrfTokenInMemory = token || null;

  if (!hasStorage()) return;

  try {
    localStorage.removeItem(LEGACY_CSRF_KEY);
  } catch {
    // Abaikan.
  }
}

export function clearSession() {
  csrfTokenInMemory = null;

  if (!hasStorage()) return;

  try {
    localStorage.removeItem(TAB_KEY);
    localStorage.removeItem(LEGACY_CSRF_KEY);
  } catch {
    // Abaikan.
  }
}

function getCsrfToken(): string | null {
  if (csrfTokenInMemory) {
    return csrfTokenInMemory;
  }

  // Fallback same-origin: cookie CSRF tidak HttpOnly sehingga bisa dibaca
  // JavaScript. Untuk deployment beda origin, token diambil dari body
  // response /auth/session lalu disimpan di memori.
  if (typeof document !== 'undefined') {
    const cookie = document.cookie
      .split('; ')
      .find((item) => item.startsWith('csrf_token='));

    if (cookie) {
      csrfTokenInMemory = decodeURIComponent(
        cookie.substring('csrf_token='.length),
      );

      return csrfTokenInMemory;
    }
  }

  return null;
}

/**
 * Simpan token CSRF yang dikirim server pada body response.
 * Response asli tidak dikonsumsi karena memakai clone().
 */
async function captureCsrfToken(response: Response) {
  const contentType = response.headers.get('content-type') ?? '';

  if (!contentType.includes('application/json')) return;

  try {
    const data = await response.clone().json();

    if (data && typeof data.csrf_token === 'string') {
      storeCsrfToken(data.csrf_token);
    }
  } catch {
    // Body bukan JSON / sudah dikonsumsi: abaikan.
  }
}

function createHeaders(init: RequestInit = {}): Headers {
  const headers = new Headers(init.headers);

  const isFormData =
    typeof FormData !== 'undefined' &&
    init.body instanceof FormData;

  if (
    init.body &&
    !headers.has('Content-Type') &&
    !isFormData
  ) {
    headers.set('Content-Type', 'application/json');
  }

  const method = (init.method ?? 'GET').toUpperCase();
  const unsafeMethod = ['POST', 'PUT', 'PATCH', 'DELETE'].includes(method);

  if (unsafeMethod) {
    const csrfToken = getCsrfToken();

    if (csrfToken) {
      headers.set('X-CSRF-Token', csrfToken);
    }
  }

  return headers;
}

interface RefreshResult {
  refreshed: boolean;
  expired: boolean;
}

let refreshInFlight: Promise<RefreshResult> | null = null;

async function requestNewAccessToken(): Promise<RefreshResult> {
  try {
    const response = await fetch(apiUrl('/auth/refresh'), {
      method: 'POST',
      credentials: 'include',
      headers: createHeaders({ method: 'POST' }),
    });

    await captureCsrfToken(response);

    if (response.status === 401 || response.status === 403) {
      return { refreshed: false, expired: true };
    }

    if (!response.ok) {
      return { refreshed: false, expired: false };
    }

    return { refreshed: true, expired: false };
  } catch {
    return { refreshed: false, expired: false };
  }
}

export function refreshAccessToken(): Promise<RefreshResult> {
  if (!refreshInFlight) {
    refreshInFlight = requestNewAccessToken().finally(() => {
      refreshInFlight = null;
    });
  }

  return refreshInFlight;
}

interface ApiFetchOptions {
  auth?: boolean;
  retryOnUnauthorized?: boolean;
}

function isAuthEndpoint(path: string): boolean {
  const normalized = path.split('?')[0].replace(/\/+$/, '');

  const authEndpoints = [
    '/auth/login',
    '/auth/register',
    '/auth/register/verify',
    '/auth/register/resend',
    '/auth/refresh',
    '/auth/session',
    '/auth/logout',
    '/auth/forgot-password',
    '/auth/forgot-password/reset',
  ];

  return authEndpoints.some((endpoint) => normalized === endpoint);
}

export async function apiFetch(
  path: string,
  init: RequestInit = {},
  options: ApiFetchOptions = {},
): Promise<Response> {
  const useAuth = options.auth !== false;
  const retryOnUnauthorized = options.retryOnUnauthorized !== false;

  const request = () =>
    fetch(apiUrl(path), {
      ...init,
      credentials: 'include',
      headers: createHeaders(init),
    });

  let response = await request();

  await captureCsrfToken(response);

  const shouldRefresh =
    useAuth &&
    retryOnUnauthorized &&
    response.status === 401 &&
    !isAuthEndpoint(path);

  if (!shouldRefresh) {
    return response;
  }

  const refreshResult = await refreshAccessToken();

  if (refreshResult.refreshed) {
    response = await request();
    await captureCsrfToken(response);
    return response;
  }

  if (refreshResult.expired) {
    clearSession();

    if (typeof window !== 'undefined') {
      window.dispatchEvent(new Event(SESSION_EXPIRED_EVENT));
    }
  }

  return response;
}
