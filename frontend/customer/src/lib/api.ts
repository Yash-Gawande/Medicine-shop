/** Thin fetch wrapper that understands the backend error envelope. */

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

export async function apiFetch<T>(path: string, init: RequestInit = {}): Promise<T> {
  const res = await fetch(`${BASE_URL}${path}`, {
    ...init,
    credentials: "include",
    headers: { Accept: "application/json", ...(init.body ? { "Content-Type": "application/json" } : {}), ...init.headers },
  });
  if (!res.ok) {
    let body: ApiErrorBody = { code: `http_${res.status}`, message: res.statusText || "Request failed" };
    try {
      const json = await res.json();
      if (json?.error) body = json.error;
    } catch {
      /* non-JSON error body */
    }
    throw new ApiError(res.status, body);
  }
  return (res.status === 204 ? undefined : await res.json()) as T;
}
