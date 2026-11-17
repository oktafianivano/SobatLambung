import { API_URL } from '../config';
import { UserProfile } from '../types';

const SESSION_KEY = 'sobat_lambung_session';
const TAB_KEY = 'sobat_lambung_active_tab';

export const SESSION_UPDATED_EVENT = 'sobatlambung:session-updated';
export const SESSION_EXPIRED_EVENT = 'sobatlambung:session-expired';

const hasStorage = () =>
  typeof window !== 'undefined' && typeof window.localStorage !== 'undefined';

/** Simpan sesi login (access token + refresh token) agar tetap masuk setelah refresh halaman. */
export function saveSession(user: UserProfile) {
  if (!hasStorage() || !user.token) return;
  localStorage.setItem(SESSION_KEY, JSON.stringify(user));
}

export function getSession(): UserProfile | null {
  if (!hasStorage()) return null;
  try {
    const raw = localStorage.getItem(SESSION_KEY);
    if (!raw) return null;
    const user = JSON.parse(raw) as UserProfile;
    return user && typeof user.id === 'number' && user.token ? user : null;
  } catch {
    return null;
  }
}

export function clearSession() {
  if (!hasStorage()) return;
  localStorage.removeItem(SESSION_KEY);
  localStorage.removeItem(TAB_KEY);
}

export function saveActiveTab(tab: string) {
  if (!hasStorage()) return;
  localStorage.setItem(TAB_KEY, tab);
}

export function getSavedActiveTab(): string | null {
  if (!hasStorage()) return null;
  return localStorage.getItem(TAB_KEY);
}

function emitSessionUpdated(user: UserProfile) {
  window.dispatchEvent(new CustomEvent<UserProfile>(SESSION_UPDATED_EVENT, { detail: user }));
}

function emitSessionExpired() {
  window.dispatchEvent(new Event(SESSION_EXPIRED_EVENT));
}

type RefreshResult = { token: string | null; expired: boolean };

let refreshInFlight: Promise<RefreshResult> | null = null;

async function requestNewAccessToken(): Promise<RefreshResult> {
  const session = getSession();
  if (!session?.refresh_token) {
    // Tidak ada refresh token (mis. sesi demo) -> anggap sesi berakhir.
    return { token: null, expired: true };
  }

  try {
    const response = await fetch(`${API_URL}/api/refresh`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ refresh_token: session.refresh_token }),
    });

    if (response.status === 401 || response.status === 403) {
      return { token: null, expired: true };
    }
    if (!response.ok) {
      // Gangguan server/jaringan: jangan hapus sesi, biarkan dicoba lagi nanti.
      return { token: null, expired: false };
    }

    const data = await response.json();
    if (!data?.access_token) {
      return { token: null, expired: true };
    }

    const current = getSession() ?? session;
    const updated: UserProfile = {
      ...current,
      token: data.access_token as string,
      refresh_token: current.refresh_token ?? session.refresh_token,
    };
    saveSession(updated);
    emitSessionUpdated(updated);
    return { token: updated.token as string, expired: false };
  } catch {
    return { token: null, expired: false };
  }
}

/**
 * Tukar refresh token menjadi access token baru.
 * Pemanggilan bersamaan akan digabung menjadi satu request saja.
 */
export function refreshAccessToken(): Promise<RefreshResult> {
  if (!refreshInFlight) {
    refreshInFlight = requestNewAccessToken().finally(() => {
      refreshInFlight = null;
    });
  }
  return refreshInFlight;
}

interface ApiFetchOptions {
  /** Kirim header Authorization dari sesi tersimpan. Default: true. */
  auth?: boolean;
  /** Coba refresh token otomatis saat menerima 401. Default: true. */
  retryOnUnauthorized?: boolean;
}

/**
 * fetch wrapper: otomatis menyisipkan access token, dan jika access token
 * kedaluwarsa (401) akan mencoba refresh token sekali lalu mengulang request.
 * Jika refresh token juga kedaluwarsa, sesi dihapus dan event logout dikirim.
 */
export async function apiFetch(
  path: string,
  init: RequestInit = {},
  options: ApiFetchOptions = {},
): Promise<Response> {
  const useAuth = options.auth !== false;
  const retryOnUnauthorized = options.retryOnUnauthorized !== false;
  const session = getSession();

  const doFetch = (token?: string) => {
    const headers: Record<string, string> = {};
    if (init.body) headers['Content-Type'] = 'application/json';
    if (init.headers) {
      new Headers(init.headers).forEach((value, key) => {
        headers[key] = value;
      });
    }
    if (useAuth && token) {
      headers['Authorization'] = `Bearer ${token}`;
    }
    return fetch(`${API_URL}${path}`, { ...init, headers });
  };

  let response = await doFetch(session?.token);

  if (useAuth && retryOnUnauthorized && response.status === 401 && session) {
    const result = await refreshAccessToken();
    if (result.token) {
      response = await doFetch(result.token);
    } else if (result.expired) {
      clearSession();
      emitSessionExpired();
    }
  }

  return response;
}
