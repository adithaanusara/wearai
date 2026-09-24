'use client';

import Link from 'next/link';
import { useSession } from '@/components/account/SessionProvider';
import { UserIcon } from '@/components/ui/icons';

export function AccountLink({ className = '' }: { className?: string }) {
  const { session } = useSession();

  return (
    <Link
      href={session ? '/account' : '/login'}
      aria-label={session ? 'My account' : 'Sign in'}
      className={`p-2 ${className}`}
    >
      <UserIcon />
    </Link>
  );
}
