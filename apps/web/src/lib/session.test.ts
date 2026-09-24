import { describe, expect, it } from 'vitest';
import { parseStoredSession } from '@/lib/session';

describe('parseStoredSession', () => {
  it('returns null when nothing is stored or the JSON is invalid', () => {
    expect(parseStoredSession(null)).toBeNull();
    expect(parseStoredSession('not json')).toBeNull();
    expect(parseStoredSession('[]')).toBeNull();
  });

  it('returns the session when name and email are present', () => {
    expect(parseStoredSession('{"name":"Nimali","email":"n@example.com"}')).toEqual({
      name: 'Nimali',
      email: 'n@example.com',
    });
  });

  it('drops extra fields and rejects incomplete sessions', () => {
    expect(parseStoredSession('{"name":"Nimali","email":"n@e.lk","password":"x"}')).toEqual({
      name: 'Nimali',
      email: 'n@e.lk',
    });
    expect(parseStoredSession('{"name":"Nimali"}')).toBeNull();
    expect(parseStoredSession('{"name":"","email":"n@e.lk"}')).toBeNull();
  });
});
