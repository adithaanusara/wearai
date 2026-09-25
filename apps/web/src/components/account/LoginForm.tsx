'use client';

import { useQueryClient } from '@tanstack/react-query';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { useRef, useState, type FormEvent } from 'react';
import { PasswordField } from '@/components/account/PasswordField';
import { SESSION_QUERY_KEY } from '@/components/account/useSession';
import { Field } from '@/components/ui/Field';
import { ApiError, login } from '@/lib/api';
import { fieldErrors, firstField } from '@/lib/form-errors';

const FIELDS = ['email', 'password'] as const;
type LoginField = (typeof FIELDS)[number];

const unreachable = 'We could not reach the store. Please try again in a moment.';

export function LoginForm() {
  const router = useRouter();
  const queryClient = useQueryClient();
  const formRef = useRef<HTMLFormElement>(null);
  // A ref, not state: a fast double click fires twice before a state update can disable the button.
  const submitting = useRef(false);
  const [values, setValues] = useState({ email: '', password: '' });
  const [errors, setErrors] = useState<Partial<Record<LoginField, string>>>({});
  const [banner, setBanner] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  function update(name: LoginField, value: string) {
    setValues((current) => ({ ...current, [name]: value }));
    setErrors((current) => ({ ...current, [name]: undefined }));
  }

  async function onSubmit(event: FormEvent) {
    event.preventDefault();
    if (submitting.current) return;
    submitting.current = true;
    setBusy(true);
    setBanner(null);
    setErrors({});

    try {
      const user = await login(values.email, values.password);
      queryClient.setQueryData(SESSION_QUERY_KEY, user);
      router.replace('/account');
      router.refresh();
    } catch (error) {
      if (error instanceof ApiError && error.status === 422) {
        const { fields, other } = fieldErrors(error.problems, FIELDS);
        setErrors(fields);
        const first = firstField(fields, FIELDS);
        if (first) formRef.current?.querySelector<HTMLElement>(`[name="${first}"]`)?.focus();
        if (other) setBanner(other);
      } else if (error instanceof ApiError && error.status < 500) {
        // For example a wrong email or password: the API gives the same message for both.
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
        disabled={busy}
        className="bg-text text-bg hover:bg-dark-2 w-full rounded-sm px-8 py-4 text-xs font-medium tracking-wide uppercase transition-colors disabled:opacity-40"
      >
        {busy ? 'Signing in…' : 'Sign in'}
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
