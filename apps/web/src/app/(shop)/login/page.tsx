import type { Metadata } from 'next';
import { AuthCard } from '@/components/account/AuthCard';
import { LoginForm } from '@/components/account/LoginForm';

export const metadata: Metadata = { title: 'Sign in' };

export default function LoginPage() {
  return (
    <AuthCard title="Sign in">
      <LoginForm />
    </AuthCard>
  );
}
