const STORAGE_KEY = "cp_deepseek_api_key";

export function getStoredKey(): string | null {
  if (typeof window === "undefined") return null;
  return window.localStorage.getItem(STORAGE_KEY);
}

export function setStoredKey(key: string) {
  if (typeof window === "undefined") return;
  window.localStorage.setItem(STORAGE_KEY, key);
}

export function clearStoredKey() {
  if (typeof window === "undefined") return;
  window.localStorage.removeItem(STORAGE_KEY);
}

export function withBYOKHeaders(headers: HeadersInit = {}): HeadersInit {
  const key = getStoredKey();
  if (!key) return headers;
  return { ...headers, "X-User-API-Key": key };
}
