import { describe, expect, it } from 'vitest';
import { needsPaymentConfirmation, paymentOutcome } from '@/lib/payment-status';

describe('paymentOutcome', () => {
  it('reads paid as confirmed and failed as failed', () => {
    expect(paymentOutcome('paid')).toBe('confirmed');
    expect(paymentOutcome('failed')).toBe('failed');
  });

  it('treats anything still in progress as pending', () => {
    expect(paymentOutcome('unpaid')).toBe('pending');
    expect(paymentOutcome('pending')).toBe('pending');
  });
});

describe('needsPaymentConfirmation', () => {
  it('is true only for card', () => {
    expect(needsPaymentConfirmation({ paymentMethod: 'card' })).toBe(true);
    expect(needsPaymentConfirmation({ paymentMethod: 'cod' })).toBe(false);
    expect(needsPaymentConfirmation({ paymentMethod: 'bank-transfer' })).toBe(false);
  });
});
