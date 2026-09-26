'use client';

import { ErrorPanel } from '@/components/layout/ErrorPanel';

export default function AdminError({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  return <ErrorPanel error={error} reset={reset} />;
}
