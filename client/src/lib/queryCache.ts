const DEFAULT_CACHE_TTL_MS = 5 * 60 * 1000;

type CacheEntry = { data: unknown; at: number };

const store = new Map<string, CacheEntry>();

export function getCacheEntry<T>(key: string, ttlMs = DEFAULT_CACHE_TTL_MS): T | null {
  const entry = store.get(key);
  if (!entry) return null;
  if (Date.now() - entry.at >= ttlMs) {
    store.delete(key);
    return null;
  }
  return entry.data as T;
}

export function setCacheEntry(key: string, data: unknown) {
  store.set(key, { data, at: Date.now() });
}

export function invalidateCache(...keys: string[]) {
  if (keys.length === 0) {
    store.clear();
    return;
  }
  for (const key of keys) {
    if (key.endsWith('*')) {
      const prefix = key.slice(0, -1);
      for (const storedKey of store.keys()) {
        if (storedKey.startsWith(prefix)) store.delete(storedKey);
      }
      continue;
    }
    store.delete(key);
  }
}

export async function cachedRequest<T>(
  key: string,
  fetcher: () => Promise<T>,
  options?: { force?: boolean; ttlMs?: number },
): Promise<T> {
  const ttlMs = options?.ttlMs ?? DEFAULT_CACHE_TTL_MS;
  if (!options?.force) {
    const hit = getCacheEntry<T>(key, ttlMs);
    if (hit !== null) return hit;
  }
  const data = await fetcher();
  setCacheEntry(key, data);
  return data;
}
