'use client';

import { useState, type FormEvent } from 'react';
import { Container } from '@/components/ui/Container';

type Status = 'idle' | 'error' | 'success';

const emailPattern = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

export function NewsletterSection() {
  const [status, setStatus] = useState<Status>('idle');

  function onSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = event.currentTarget;
    const email = String(new FormData(form).get('email') ?? '').trim();

    if (!emailPattern.test(email)) {
      setStatus('error');
      return;
    }
    // The API endpoint is connected when the backend exists.
    setStatus('success');
    form.reset();
  }

  return (
    <section aria-labelledby="newsletter-title" className="bg-surface">
      <Container className="flex flex-col items-center gap-6 py-16 text-center md:py-20">
        <h2
          id="newsletter-title"
          className="text-2xl font-bold tracking-wide uppercase md:text-3xl"
        >
          Sign up now
        </h2>
        <p className="text-muted max-w-md text-sm">
          Be the first to hear about new drops, restocks and exclusive offers.
        </p>

        <form onSubmit={onSubmit} noValidate className="w-full max-w-md">
          <div className="flex flex-col gap-3 sm:flex-row">
            <label htmlFor="newsletter-email" className="sr-only">
              Email address
            </label>
            <input
              id="newsletter-email"
              name="email"
              type="email"
              autoComplete="email"
              placeholder="Email address"
              aria-invalid={status === 'error'}
              aria-describedby="newsletter-message"
              className="border-border bg-bg placeholder:text-muted w-full flex-1 rounded-sm border px-4 py-3 text-sm"
            />
            <button
              type="submit"
              className="bg-text text-bg rounded-sm px-6 py-3 text-sm font-medium tracking-wide uppercase"
            >
              Sign up
            </button>
          </div>
          <p
            id="newsletter-message"
            role="status"
            className={`mt-3 min-h-5 text-sm ${status === 'error' ? 'text-error' : 'text-success'}`}
          >
            {status === 'error' && 'Please enter a valid email address.'}
            {status === 'success' && 'Thanks for signing up!'}
          </p>
        </form>
      </Container>
    </section>
  );
}
