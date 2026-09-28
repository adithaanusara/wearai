import { describe, expect, it } from 'vitest';
import { cleanCode } from '@/lib/two-factor';

describe('cleanCode', () => {
  it('strips whitespace from a numeric authenticator code', () => {
    expect(cleanCode('123 456')).toBe('123456');
    expect(cleanCode(' 123456 ')).toBe('123456');
  });

  it('leaves a recovery code as typed, aside from surrounding whitespace', () => {
    expect(cleanCode(' ABCD-1234 ')).toBe('ABCD-1234');
  });
});
