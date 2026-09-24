'use client';

import { useSyncExternalStore } from 'react';

const subscribe = () => () => {};

/** False on the server and during hydration, true afterwards. Use it to avoid flashing empty client-only data. */
export function useHydrated(): boolean {
  return useSyncExternalStore(
    subscribe,
    () => true,
    () => false,
  );
}
