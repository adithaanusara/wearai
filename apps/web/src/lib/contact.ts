export interface ContactValues {
  name: string;
  email: string;
  message: string;
}

export type ContactErrors = Partial<Record<keyof ContactValues, string>>;

export const MIN_MESSAGE_LENGTH = 10;

const emailPattern = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

export function validateContact(values: ContactValues): ContactErrors {
  const errors: ContactErrors = {};
  if (!values.name.trim()) errors.name = 'Enter your name.';
  if (!emailPattern.test(values.email.trim())) errors.email = 'Enter a valid email address.';
  if (values.message.trim().length < MIN_MESSAGE_LENGTH) {
    errors.message = `Write at least ${MIN_MESSAGE_LENGTH} characters so we can help.`;
  }
  return errors;
}
