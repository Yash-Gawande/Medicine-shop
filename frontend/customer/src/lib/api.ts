/** Thin fetch wrapper: backend error envelope, bearer token, single-flight refresh on 401. */
import type { TokenResponse } from "@/lib/auth-types";

const BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "/api/v1";

export interface ApiErrorBody {
  code: string;
  message: string;
  details?: unknown;
  request_id?: string;
}

export class ApiError extends Error {
  readonly status: number;
  readonly code: string;
  readonly details?: unknown;
  readonly requestId?: string;

  constructor(status: number, body: ApiErrorBody) {
    super(body.message);
    this.status = status;
    this.code = body.code;
    this.details = body.details;
    this.requestId = body.request_id;
  }
}

// The access token lives in memory only; the refresh token is an httpOnly cookie.
let accessToken: string | null = null;
let onSessionLost: (() => void) | null = null;
let inflightRefresh: Promise<TokenResponse | null> | null = null;

export const setAccessToken = (token: string | null) => {
  accessToken = token;
};
export const setSessionLostHandler = (fn: (() => void) | null) => {
  onSessionLost = fn;
};

async function errorFrom(res: Response): Promise<ApiError> {
  let body: ApiErrorBody = { code: `http_${res.status}`, message: res.statusText || "Request failed" };
  try {
    const json = await res.json();
    if (json?.error) body = json.error;
  } catch {
    /* non-JSON error body */
  }
  return new ApiError(res.status, body);
}

/**
 * Exchanges the refresh cookie for a new session. Single-flight: the backend treats a
 * replayed (already rotated) refresh token as theft and revokes the session, so concurrent
 * callers (StrictMode double effects, parallel 401s) must share one request.
 */
export function refreshSession(): Promise<TokenResponse | null> {
  inflightRefresh ??= (async () => {
    try {
      const res = await fetch(`${BASE_URL}/auth/refresh`, {
        method: "POST",
        credentials: "include",
        headers: { Accept: "application/json" },
      });
      if (!res.ok) return null;
      const data = (await res.json()) as TokenResponse;
      accessToken = data.access_token;
      return data;
    } catch {
      return null;
    } finally {
      inflightRefresh = null;
    }
  })();
  return inflightRefresh;
}

export interface ApiRequestInit extends RequestInit {
  /** Don't try to refresh on 401 (used by the auth endpoints themselves). */
  skipRefresh?: boolean;
}

export async function apiFetch<T>(path: string, init: ApiRequestInit = {}): Promise<T> {
  const { skipRefresh, ...rest } = init;
  const send = () =>
    fetch(`${BASE_URL}${path}`, {
      ...rest,
      credentials: "include",
      headers: {
        Accept: "application/json",
        ...(rest.body ? { "Content-Type": "application/json" } : {}),
        ...(accessToken ? { Authorization: `Bearer ${accessToken}` } : {}),
        ...rest.headers,
      },
    });

  let res = await send();
  if (res.status === 401 && !skipRefresh && accessToken) {
    const refreshed = await refreshSession();
    if (refreshed) res = await send();
    else {
      accessToken = null;
      onSessionLost?.();
    }
  }
  if (!res.ok) throw await errorFrom(res);
  return (res.status === 204 ? undefined : await res.json()) as T;
}
