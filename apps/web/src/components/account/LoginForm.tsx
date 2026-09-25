'use client';

import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { useRef, useState, type FormEvent } from 'react';
import { useSession } from '@/components/account/SessionProvider';
import { PasswordField } from '@/components/account/PasswordField';
import { Field } from '@/components/ui/Field';
import { validateLogin, type LoginErrors, type LoginValues } from '@/lib/auth';

const fieldOrder: (keyof LoginValues)[] = ['email', 'password'];

/** "nimali.perera@example.com" becomes "Nimali Perera". Only used until the API returns the real name. */
function nameFromEmail(email: string): string {
  const local = email
    .split('@')[0]
    .replace(/[._-]+/g, ' ')
    .trim();
  return local.replace(/\b\w/g, (letter) => letter.toUpperCase()) || 'Customer';
}

export function LoginForm() {
  const router = useRouter();
  const { signIn } = useSession();
  const formRef = useRef<HTMLFormElement>(null);
  const [values, setValues] = useState<LoginValues>({ email: '', password: '' });
  const [errors, setErrors] = useState<LoginErrors>({});

  function update(name: keyof LoginValues, value: string) {
    setValues((current) => ({ ...current, [name]: value }));
    setErrors((current) => ({ ...current, [name]: undefined }));
  }

  function onSubmit(event: FormEvent) {
    event.preventDefault();
    const found = validateLogin(values);
    setErrors(found);

    const firstInvalid = fieldOrder.find((name) => found[name]);
    if (firstInvalid) {
      formRef.current?.querySelector<HTMLElement>(`[name="${firstInvalid}"]`)?.focus();
      return;
    }

    const email = values.email.trim();
    signIn({ name: nameFromEmail(email), email });
    router.push('/account');
  }

  return (
    <form ref={formRef} onSubmit={onSubmit} noValidate className="space-y-4">
      <Field
        name="email"
        label="Email"
        type="email"
        autoComplete="email"
        value={values.email}
        error={errors.email}
        onChange={(event) => update('email', event.target.value)}
      />
      <PasswordField
        name="password"
        label="Password"
        autoComplete="current-password"
        value={values.password}
        error={errors.password}
        onChange={(event) => update('password', event.target.value)}
      />
      <button
        type="submit"
        className="bg-text text-bg hover:bg-dark-2 w-full rounded-sm px-8 py-4 text-xs font-medium tracking-wide uppercase transition-colors"
      >
        Sign in
      </button>
      <p className="text-sm">
        New here?{' '}
        <Link href="/register" className="underline">
          Create an account
        </Link>
      </p>
    </form>
  );
}
