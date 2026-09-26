'use client';

import { useQueryClient } from '@tanstack/react-query';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { useRef, useState, type FormEvent } from 'react';
import { PasswordField } from '@/components/account/PasswordField';
import { SESSION_QUERY_KEY } from '@/components/account/useSession';
import { Field } from '@/components/ui/Field';
import { ApiError, register } from '@/lib/api';
import { fieldErrors, firstField } from '@/lib/form-errors';

const FIELDS = ['name', 'email', 'password', 'confirmPassword'] as const;
type RegisterField = (typeof FIELDS)[number];

const unreachable = 'We could not reach the store. Please try again in a moment.';

export function RegisterForm() {
  const router = useRouter();
  const queryClient = useQueryClient();
  const formRef = useRef<HTMLFormElement>(null);
  const submitting = useRef(false);
  const [values, setValues] = useState({ name: '', email: '', password: '', confirmPassword: '' });
  const [errors, setErrors] = useState<Partial<Record<RegisterField, string>>>({});
  const [banner, setBanner] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  function update(name: RegisterField, value: string) {
    setValues((current) => ({ ...current, [name]: value }));
    setErrors((current) => ({ ...current, [name]: undefined }));
  }

  function show(problems: Partial<Record<RegisterField, string>>) {
    setErrors(problems);
    const first = firstField(problems, FIELDS);
    if (first) formRef.current?.querySelector<HTMLElement>(`[name="${first}"]`)?.focus();
  }

  async function onSubmit(event: FormEvent) {
    event.preventDefault();
    if (submitting.current) return;

    // The one rule the API cannot check: it never receives the confirmation.
    if (values.confirmPassword !== values.password) {
      setBanner(null);
      show({ confirmPassword: 'The passwords do not match.' });
      return;
    }

    submitting.current = true;
    setBusy(true);
    setBanner(null);
    setErrors({});

    try {
      const user = await register(values.name, values.email, values.password);
      queryClient.setQueryData(SESSION_QUERY_KEY, user);
      router.replace('/account');
      router.refresh();
    } catch (error) {
      if (error instanceof ApiError && error.status === 409) {
        show({ email: error.message });
      } else if (error instanceof ApiError && error.status === 422) {
        const { fields, other } = fieldErrors(error.problems, FIELDS);
        show(fields);
        if (other) setBanner(other);
      } else if (error instanceof ApiError && error.status < 500) {
        setBanner(error.message);
      } else {
        setBanner(unreachable);
      }
    } finally {
      submitting.current = false;
      setBusy(false);
    }
  }

  return (
    <form ref={formRef} onSubmit={onSubmit} noValidate className="space-y-4">
      {banner && (
        <p role="alert" className="border-error text-error rounded-sm border p-3 text-sm">
          {banner}
        </p>
      )}
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
      <p className="text-muted -mt-2 text-xs">At least 8 characters, with a letter and a number.</p>
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
        disabled={busy}
        className="bg-text text-bg hover:bg-dark-2 w-full rounded-sm px-8 py-4 text-xs font-medium tracking-wide uppercase transition-colors disabled:opacity-40"
      >
        {busy ? 'Creating account…' : 'Create account'}
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
