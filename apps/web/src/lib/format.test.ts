import { describe, expect, it } from 'vitest';
import { formatPrice } from '@/lib/format';

describe('formatPrice', () => {
  it('formats whole rupees with two decimals and the currency code', () => {
    expect(formatPrice(4450)).toBe('LKR 4,450.00');
  });

  it('groups thousands', () => {
    expect(formatPrice(125000)).toBe('LKR 125,000.00');
  });

  it('formats zero', () => {
    expect(formatPrice(0)).toBe('LKR 0.00');
  });
});
