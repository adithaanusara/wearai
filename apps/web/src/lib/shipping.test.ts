import { describe, expect, it } from 'vitest';
import { calculateShipping } from '@/lib/shipping';

describe('calculateShipping', () => {
  it('charges the standard fee below the free-shipping threshold', () => {
    expect(calculateShipping(5000, 'standard')).toBe(450);
    expect(calculateShipping(14999, 'standard')).toBe(450);
  });

  it('makes standard delivery free at and above the threshold', () => {
    expect(calculateShipping(15000, 'standard')).toBe(0);
    expect(calculateShipping(40000, 'standard')).toBe(0);
  });

  it('always charges express, even for large orders', () => {
    expect(calculateShipping(40000, 'express')).toBe(950);
  });

  it('does not charge for store pickup', () => {
    expect(calculateShipping(1000, 'pickup')).toBe(0);
  });

  it('treats an unknown method as free', () => {
    expect(calculateShipping(1000, 'drone')).toBe(0);
  });
});
