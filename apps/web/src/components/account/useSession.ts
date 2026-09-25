'use client';

import { useQuery } from '@tanstack/react-query';
import { getMe } from '@/lib/api';

export const SESSION_QUERY_KEY = ['session'];

/**
 * Who is signed in, according to the server. The session cookie is HttpOnly, so scripts on the page
 * never see it: they can only ask the API. `session` is null when nobody is signed in or while
 * the answer is still loading.
 */
export function useSession() {
  const query = useQuery({
    queryKey: SESSION_QUERY_KEY,
    queryFn: () => getMe(),
    staleTime: 60_000,
    retry: false,
  });

  return { session: query.data ?? null, isLoading: query.isPending };
}
