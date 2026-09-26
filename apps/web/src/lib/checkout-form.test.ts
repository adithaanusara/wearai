import { describe, expect, it } from 'vitest';
import { ApiError } from '@/lib/api';
import {
  firstInvalidField,
  mapProblems,
  priceChangedMessage,
  readPriceChange,
} from '@/lib/checkout-form';

const problem = (loc: (string | number)[], msg: string) => ({ loc, msg });

describe('mapProblems', () => {
  it('puts each problem on its form field', () => {
    const mapped = mapProblems([
      problem(['body', 'email'], 'Enter a valid email address.'),
      problem(['body', 'postalCode'], 'Enter a 5-digit postal code.'),
    ]);

    expect(mapped.fields).toEqual({
      email: 'Enter a valid email address.',
      postalCode: 'Enter a 5-digit postal code.',
    });
    expect(mapped.cartProblem).toBe(false);
    expect(mapped.other).toBeNull();
  });

  it('keeps the first message when a field has several', () => {
    const mapped = mapProblems([
      problem(['body', 'phone'], 'First'),
      problem(['body', 'phone'], 'Second'),
    ]);

    expect(mapped.fields.phone).toBe('First');
  });

  it('treats problems on cart lines as a cart problem, not a form error', () => {
    const mapped = mapProblems([
      problem(['body', 'items', 1, 'size'], 'This size is not available.'),
    ]);

    expect(mapped.cartProblem).toBe(true);
    expect(mapped.fields).toEqual({});
  });

  it('collects problems that belong to no field', () => {
    const mapped = mapProblems([
      problem(['body'], 'Something is off.'),
      problem(['body', 'mystery'], 'Later'),
    ]);

    expect(mapped.other).toBe('Something is off.');
    expect(mapped.fields).toEqual({});
  });

  it('handles no problems', () => {
    expect(mapProblems([])).toEqual({ fields: {}, cartProblem: false, other: null });
  });
});

describe('firstInvalidField', () => {
  it('follows the order of the page, not the order of the errors', () => {
    expect(firstInvalidField({ postalCode: 'x', phone: 'y', city: 'z' })).toBe('phone');
  });

  it('returns undefined when there are no errors', () => {
    expect(firstInvalidField({})).toBeUndefined();
  });
});

describe('readPriceChange', () => {
  const change = (total: unknown) =>
    new ApiError(409, 'changed', [], { code: 'price_changed', details: { total } });

  it('returns the new total for a price change', () => {
    expect(readPriceChange(change(8450))).toBe(8450);
    expect(readPriceChange(change(0))).toBe(0);
  });

  it('is null for every other kind of failure', () => {
    expect(
      readPriceChange(new ApiError(409, 'x', [], { code: 'idempotency_conflict' })),
    ).toBeNull();
    expect(readPriceChange(new ApiError(422, 'x', [], { code: 'price_changed' }))).toBeNull();
    expect(readPriceChange(new ApiError(503, 'down'))).toBeNull();
    expect(readPriceChange(new Error('boom'))).toBeNull();
    expect(readPriceChange(null)).toBeNull();
  });

  it('is null when the API did not say what the new total is', () => {
    expect(readPriceChange(change(undefined))).toBeNull();
    expect(readPriceChange(change('8450'))).toBeNull();
  });
});

describe('priceChangedMessage', () => {
  it('shows the new total in LKR and says nothing was placed', () => {
    const message = priceChangedMessage(8450);

    expect(message).toContain('LKR 8,450.00');
    expect(message).toMatch(/place the order again/);
  });
});
