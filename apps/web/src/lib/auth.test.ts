import { describe, expect, it } from 'vitest';
import {
  checkPasswordStrength,
  validateLogin,
  validateRegister,
  type RegisterValues,
} from '@/lib/auth';

describe('checkPasswordStrength', () => {
  it('rejects short passwords', () => {
    expect(checkPasswordStrength('abc12')).toMatch(/at least 8/);
  });

  it('requires a letter and a number', () => {
    expect(checkPasswordStrength('abcdefgh')).toMatch(/letter and one number/);
    expect(checkPasswordStrength('12345678')).toMatch(/letter and one number/);
  });

  it('accepts a password with letters and numbers', () => {
    expect(checkPasswordStrength('sunrise2026')).toBeUndefined();
  });
});

describe('validateLogin', () => {
  it('accepts an email and any password', () => {
    expect(validateLogin({ email: 'a@b.lk', password: 'x' })).toEqual({});
  });

  it('flags a bad email and an empty password', () => {
    expect(validateLogin({ email: 'nope', password: '' })).toEqual({
      email: expect.any(String),
      password: expect.any(String),
    });
  });
});

describe('validateRegister', () => {
  const valid: RegisterValues = {
    name: 'Nimali Perera',
    email: 'nimali@example.com',
    password: 'sunrise2026',
    confirmPassword: 'sunrise2026',
  };

  it('accepts valid details', () => {
    expect(validateRegister(valid)).toEqual({});
  });

  it('requires a name', () => {
    expect(validateRegister({ ...valid, name: '  ' }).name).toBeDefined();
  });

  it('applies the password rules', () => {
    const errors = validateRegister({ ...valid, password: 'short1', confirmPassword: 'short1' });
    expect(errors.password).toBeDefined();
  });

  it('requires the confirmation to match', () => {
    expect(
      validateRegister({ ...valid, confirmPassword: 'sunrise2027' }).confirmPassword,
    ).toBeDefined();
  });
});
