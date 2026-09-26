import { describe, expect, it } from 'vitest';
import { statusLabel } from '@/lib/orders';

describe('statusLabel', () => {
  it('capitalises the first letter', () => {
    expect(statusLabel('pending')).toBe('Pending');
    expect(statusLabel('delivered')).toBe('Delivered');
  });

  it('leaves an empty or already capitalised status alone', () => {
    expect(statusLabel('')).toBe('');
    expect(statusLabel('Shipped')).toBe('Shipped');
  });
});
