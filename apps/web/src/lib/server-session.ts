import { cookies } from 'next/headers';
import { getMe } from '@/lib/api';
import type { User } from '@/types/api';

/** The request's cookies, ready to pass to the API so it can tell who is signed in. */
export async function serverAuthHeaders(): Promise<Record<string, string>> {
  const cookie = (await cookies()).toString();
  return cookie ? { Cookie: cookie } : {};
}

/** The signed-in user for the current request, or null. For server components only. */
export async function getServerSession(): Promise<User | null> {
  return getMe(await serverAuthHeaders());
}
