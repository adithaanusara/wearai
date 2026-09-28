/** Only digits, whitespace stripped: what an authenticator app shows, cleaned up before it is sent. */
export function cleanAuthenticatorCode(value: string): string {
  return value.replace(/\s+/g, '');
}

/** A recovery code (XXXX-XXXX) is left as typed, since it is not purely numeric. */
export function cleanCode(value: string): string {
  const trimmed = value.trim();
  return /^[0-9\s]+$/.test(trimmed) ? cleanAuthenticatorCode(trimmed) : trimmed;
}
