export interface LoginValues {
  email: string;
  password: string;
}

export interface RegisterValues {
  name: string;
  email: string;
  password: string;
  confirmPassword: string;
}

export type LoginErrors = Partial<Record<keyof LoginValues, string>>;
export type RegisterErrors = Partial<Record<keyof RegisterValues, string>>;

export const MIN_PASSWORD_LENGTH = 8;

const emailPattern = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

/** Returns a message when the password is too weak, or undefined when it is fine. */
export function checkPasswordStrength(password: string): string | undefined {
  if (password.length < MIN_PASSWORD_LENGTH) {
    return `Use at least ${MIN_PASSWORD_LENGTH} characters.`;
  }
  if (!/[a-zA-Z]/.test(password) || !/\d/.test(password)) {
    return 'Use at least one letter and one number.';
  }
  return undefined;
}

// Login only checks that something was entered; strength rules apply when choosing a password.
export function validateLogin(values: LoginValues): LoginErrors {
  const errors: LoginErrors = {};
  if (!emailPattern.test(values.email.trim())) errors.email = 'Enter a valid email address.';
  if (!values.password) errors.password = 'Enter your password.';
  return errors;
}

export function validateRegister(values: RegisterValues): RegisterErrors {
  const errors: RegisterErrors = {};
  if (!values.name.trim()) errors.name = 'Enter your name.';
  if (!emailPattern.test(values.email.trim())) errors.email = 'Enter a valid email address.';

  const passwordProblem = checkPasswordStrength(values.password);
  if (passwordProblem) errors.password = passwordProblem;

  if (values.confirmPassword !== values.password) {
    errors.confirmPassword = 'The passwords do not match.';
  }
  return errors;
}
