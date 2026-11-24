
import { apiUrl } from '../services/api';

const TAB_KEY = 'sobat_lambung_active_tab';
const CSRF_KEY = 'sobat_lambung_csrf_token';

export const SESSION_UPDATED_EVENT = 'sobatlambung:session-updated';
export const SESSION_EXPIRED_EVENT = 'sobatlambung:session-expired';

const hasStorage = () =>
  typeof window !== 'undefined' &&
  typeof window.localStorage !== 'undefined';

export function saveActiveTab(tab: string) {
  if (!hasStorage()) return;
  localStorage.setItem(TAB_KEY, tab);
}

export function getSavedActiveTab(): string | null {
  if (!hasStorage()) return null;
  return localStorage.getItem(TAB_KEY);
}

export function storeCsrfToken(token: string | null | undefined) {
  if (!hasStorage() || !token) return;
  localStorage.setItem(CSRF_KEY, token);
}

export function clearSession() {
  if (!hasStorage()) return;
  localStorage.removeItem(TAB_KEY);
  localStorage.removeItem(CSRF_KEY);
}

function getCsrfToken(): string | null {
  if (typeof document !== 'undefined') {
    const cookie = document.cookie
      .split('; ')
      .find((item) => item.startsWith('csrf_token='));

    if (cookie) {
      return decodeURIComponent(
        cookie.substring('csrf_token='.length),
      );
    }
  }

  // Deployment beda origin: cookie API tidak bisa dibaca JavaScript.
  // Token dari body response login/refresh disimpan di localStorage.
  if (hasStorage()) {
    return localStorage.getItem(CSRF_KEY);
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
