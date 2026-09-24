import type { Metadata } from 'next';
import { AccountView } from '@/components/account/AccountView';
import { Container } from '@/components/ui/Container';

export const metadata: Metadata = { title: 'My account' };

export default function AccountPage() {
  return (
    <Container className="py-10 md:py-14">
      <h1 className="text-3xl font-bold tracking-wide uppercase md:text-4xl">My account</h1>
      <div className="max-w-2xl">
        <AccountView />
      </div>
    </Container>
  );
}
