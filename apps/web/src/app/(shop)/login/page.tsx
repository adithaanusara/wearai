import type { Metadata } from 'next';
import { redirect } from 'next/navigation';
import { AuthCard } from '@/components/account/AuthCard';
import { LoginForm } from '@/components/account/LoginForm';
import { getServerSession } from '@/lib/server-session';

export const metadata: Metadata = { title: 'Sign in' };

// Whether to show this page depends on the visitor's session, so it renders on every request.
export const dynamic = 'force-dynamic';

export default async function LoginPage() {
  // If the store service is down the form still shows; submitting it explains the problem.
  const user = await getServerSession().catch(() => null);
  if (user) redirect('/account');

  return (
    <AuthCard title="Sign in">
      <LoginForm />
    </AuthCard>
  );
}
