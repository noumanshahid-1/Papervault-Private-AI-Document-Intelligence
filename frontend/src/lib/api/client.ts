export async function request<T>(
  url: string,
  init?: RequestInit,
): Promise<T> {
  const response = await fetch(url, init);
  if (!response.ok) {
    const body = await response.text().catch(() => response.statusText);
    throw new Error(body || `HTTP ${response.status}`);
  }
  return response.json() as Promise<T>;
}
