export async function apiJson<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`/api/aurora${path}`, { credentials: "include", ...init });
  if (!res.ok) {
    const text = await res.text().catch(() => "");
    throw new Error(text || `${res.status} ${res.statusText}`);
  }
  return (await res.json()) as T;
}
