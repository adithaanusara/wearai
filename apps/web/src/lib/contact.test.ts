import { describe, expect, it } from 'vitest';
import { validateContact } from '@/lib/contact';

const valid = { name: 'Nimali', email: 'nimali@example.com', message: 'Where is my order?' };

describe('validateContact', () => {
  it('accepts a complete message', () => {
    expect(validateContact(valid)).toEqual({});
  });

  it('requires a name and a valid email', () => {
    const errors = validateContact({ ...valid, name: ' ', email: 'nimali' });
    expect(Object.keys(errors).sort()).toEqual(['email', 'name']);
  });

  it('requires a meaningful message and ignores surrounding spaces', () => {
    expect(validateContact({ ...valid, message: 'hi' }).message).toBeDefined();
    expect(validateContact({ ...valid, message: '   hi   ' }).message).toBeDefined();
    expect(validateContact({ ...valid, message: '1234567890' }).message).toBeUndefined();
  });
});
