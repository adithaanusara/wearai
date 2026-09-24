import { describe, expect, it } from 'vitest';
import { formatDate, formatPrice } from '@/lib/format';

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

describe('formatDate', () => {
  it('formats an ISO date in day-month-year order', () => {
    expect(formatDate('2026-09-12')).toBe('12 September 2026');
  });

  it('does not shift the day with the local time zone', () => {
    expect(formatDate('2026-01-01')).toBe('1 January 2026');
  });
});
