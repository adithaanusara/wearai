import type { Metadata } from 'next';
import { AuthCard } from '@/components/account/AuthCard';
import { RegisterForm } from '@/components/account/RegisterForm';

export const metadata: Metadata = { title: 'Create account' };

export default function RegisterPage() {
  return (
    <AuthCard title="Create account">
      <RegisterForm />
    </AuthCard>
  );
}
