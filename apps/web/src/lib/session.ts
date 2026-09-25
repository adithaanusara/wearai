export interface Session {
  name: string;
  email: string;
}

/** Reads a saved session, returning null for anything that is not a well-formed session. */
export function parseStoredSession(raw: string | null): Session | null {
  if (!raw) return null;
  try {
    const data: unknown = JSON.parse(raw);
    if (typeof data !== 'object' || data === null) return null;
    const { name, email } = data as Record<string, unknown>;
    if (typeof name !== 'string' || typeof email !== 'string' || !name || !email) return null;
    return { name, email };
  } catch {
    return null;
  }
}
