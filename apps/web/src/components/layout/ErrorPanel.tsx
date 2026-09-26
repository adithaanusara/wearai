'use client';

import { useRouter } from 'next/navigation';
import { startTransition } from 'react';
import { Container } from '@/components/ui/Container';

/** Shown when a page cannot load its data, for example when the store service is down. */
export function ErrorPanel({ error, reset }: { error: Error; reset: () => void }) {
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

      {/* Server errors are hidden in production, so this only ever shows while developing. */}
      {process.env.NODE_ENV === 'development' && (
        <div className="border-border max-w-xl space-y-2 rounded-sm border p-4 text-left text-xs">
          <p className="font-medium">Development details</p>
          <p className="text-muted break-words">{error.message}</p>
          <p>
            Pages load their data from the API. If it is not running, start the database with{' '}
            <code>pnpm db</code> and the API with <code>pnpm dev:api</code>.
          </p>
        </div>
      )}
    </Container>
  );
}
