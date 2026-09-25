import { describe, expect, it } from 'vitest';
import { fieldErrors, firstField } from '@/lib/form-errors';

const fields = ['name', 'email', 'password'] as const;
const problem = (loc: (string | number)[], msg: string) => ({ loc, msg });

describe('fieldErrors', () => {
  it('puts each problem on its field', () => {
    const result = fieldErrors(
      [
        problem(['body', 'email'], 'Enter a valid email address.'),
        problem(['body', 'password'], 'Too short.'),
      ],
      fields,
    );

    expect(result.fields).toEqual({
      email: 'Enter a valid email address.',
      password: 'Too short.',
    });
    expect(result.other).toBeNull();
  });

  it('keeps the first message for a field', () => {
    const result = fieldErrors(
      [problem(['body', 'name'], 'First'), problem(['body', 'name'], 'Second')],
      fields,
    );

    expect(result.fields.name).toBe('First');
  });

  it('collects problems that belong to no known field', () => {
    const result = fieldErrors(
      [problem(['body'], 'Odd'), problem(['body', 'extra'], 'Later')],
      fields,
    );

    expect(result.fields).toEqual({});
    expect(result.other).toBe('Odd');
  });

  it('handles no problems', () => {
    expect(fieldErrors([], fields)).toEqual({ fields: {}, other: null });
  });
});

describe('firstField', () => {
  it('follows the order of the form, not of the errors', () => {
    expect(firstField({ password: 'x', email: 'y' }, fields)).toBe('email');
  });

  it('returns undefined when nothing is wrong', () => {
    expect(firstField({}, fields)).toBeUndefined();
  });
});
