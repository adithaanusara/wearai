'use client';

import { usePathname, useRouter, useSearchParams } from 'next/navigation';

/** Lets filter controls change the URL query string; the server page re-renders from it. */
export function useQueryUpdater() {
  const router = useRouter();
  const pathname = usePathname();
  const searchParams = useSearchParams();

  function update(change: (params: URLSearchParams) => void) {
    const params = new URLSearchParams(searchParams.toString());
    change(params);
    // A different filter or sort means a different result list, so start again from page 1.
    params.delete('page');
    const query = params.toString();
    router.replace(query ? `${pathname}?${query}` : pathname, { scroll: false });
  }

  return { update, queryKey: searchParams.toString() };
}
