'use client';

import { useRouter } from 'next/navigation';
import { startTransition } from 'react';
import { Container } from '@/components/ui/Container';

/** Shown when a page cannot load its data, for example when the store service is down. */
export function ErrorPanel({ reset }: { reset: () => void }) {
  const router = useRouter();

  function retry() {
    // reset() alone only re-renders with the failed result; refresh() fetches the page again.
    startTransition(() => {
      router.refresh();
      reset();
    });
  }

  return (
    <Container className="flex flex-1 flex-col items-center justify-center gap-6 py-24 text-center">
      <h1 className="text-3xl font-bold tracking-wide uppercase">Something went wrong</h1>
      <p className="text-muted max-w-md text-sm">
        We could not load this page. Please try again in a moment.
      </p>
      <button
        type="button"
        onClick={retry}
        className="bg-text text-bg hover:bg-dark-2 rounded-sm px-8 py-3 text-xs font-medium tracking-wide uppercase transition-colors"
      >
        Try again
      </button>
    </Container>
  );
}
