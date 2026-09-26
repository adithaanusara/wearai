import { cookies } from 'next/headers';
import { notFound, redirect } from 'next/navigation';
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

const rank = { customer: 0, staff: 1, admin: 2 } as const;

/**
 * For admin pages: sends a visitor who is not signed in to the login page, and shows the ordinary
 * "not found" page to a signed-in user without the role, so the admin area does not advertise itself.
 * This only decides what the website shows. Every admin API call checks the role again.
 */
export async function requireRole(minimum: keyof typeof rank): Promise<User> {
  const user = await getServerSession();
  if (!user) redirect('/login');
  if (rank[user.role] < rank[minimum]) notFound();
  return user;
}
