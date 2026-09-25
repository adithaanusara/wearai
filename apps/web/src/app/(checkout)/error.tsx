'use client';

import { ErrorPanel } from '@/components/layout/ErrorPanel';

export default function ErrorPage({
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  return <ErrorPanel reset={reset} />;
}
