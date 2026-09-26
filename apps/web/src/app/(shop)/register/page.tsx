import type { Metadata } from 'next';
import { redirect } from 'next/navigation';
import { AuthCard } from '@/components/account/AuthCard';
import { RegisterForm } from '@/components/account/RegisterForm';
import { getServerSession } from '@/lib/server-session';

export const metadata: Metadata = { title: 'Create account' };

// Whether to show this page depends on the visitor's session, so it renders on every request.
export const dynamic = 'force-dynamic';

export default async function RegisterPage() {
  // If the store service is down the form still shows; submitting it explains the problem.
  const user = await getServerSession().catch(() => null);
  if (user) redirect('/account');

  return (
    <AuthCard title="Create account">
      <RegisterForm />
    </AuthCard>
  );
}
