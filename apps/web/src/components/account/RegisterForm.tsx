'use client';

import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { useRef, useState, type FormEvent } from 'react';
import { PasswordField } from '@/components/account/PasswordField';
import { useSession } from '@/components/account/SessionProvider';
import { Field } from '@/components/ui/Field';
import {
  MIN_PASSWORD_LENGTH,
  validateRegister,
  type RegisterErrors,
  type RegisterValues,
} from '@/lib/auth';

const fieldOrder: (keyof RegisterValues)[] = ['name', 'email', 'password', 'confirmPassword'];

export function RegisterForm() {
  const router = useRouter();
  const { signIn } = useSession();
  const formRef = useRef<HTMLFormElement>(null);
  const [values, setValues] = useState<RegisterValues>({
    name: '',
    email: '',
    password: '',
    confirmPassword: '',
  });
  const [errors, setErrors] = useState<RegisterErrors>({});

  function update(name: keyof RegisterValues, value: string) {
    setValues((current) => ({ ...current, [name]: value }));
    setErrors((current) => ({ ...current, [name]: undefined }));
  }

  function onSubmit(event: FormEvent) {
    event.preventDefault();
    const found = validateRegister(values);
    setErrors(found);

    const firstInvalid = fieldOrder.find((name) => found[name]);
    if (firstInvalid) {
      formRef.current?.querySelector<HTMLElement>(`[name="${firstInvalid}"]`)?.focus();
      return;
    }

    // The password is checked and then discarded; only the name and email are kept in this demo.
    signIn({ name: values.name.trim(), email: values.email.trim() });
    router.push('/account');
  }

  return (
    <form ref={formRef} onSubmit={onSubmit} noValidate className="space-y-4">
      <Field
        name="name"
        label="Full name"
        autoComplete="name"
        value={values.name}
        error={errors.name}
        onChange={(event) => update('name', event.target.value)}
      />
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
        autoComplete="new-password"
        value={values.password}
        error={errors.password}
        onChange={(event) => update('password', event.target.value)}
      />
      <p className="text-muted -mt-2 text-xs">
        At least {MIN_PASSWORD_LENGTH} characters, with a letter and a number.
      </p>
      <PasswordField
        name="confirmPassword"
        label="Confirm password"
        autoComplete="new-password"
        value={values.confirmPassword}
        error={errors.confirmPassword}
        onChange={(event) => update('confirmPassword', event.target.value)}
      />
      <button
        type="submit"
        className="bg-text text-bg hover:bg-dark-2 w-full rounded-sm px-8 py-4 text-xs font-medium tracking-wide uppercase transition-colors"
      >
        Create account
      </button>
      <p className="text-sm">
        Already have an account?{' '}
        <Link href="/login" className="underline">
          Sign in
        </Link>
      </p>
    </form>
  );
}
