import { describe, expect, it } from 'vitest';
import { firstInvalidField, mapProblems } from '@/lib/checkout-form';

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
