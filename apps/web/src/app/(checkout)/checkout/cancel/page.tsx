import type { Metadata } from 'next';
import { CancelledOrderNotice } from '@/components/checkout/CancelledOrderNotice';
import { Container } from '@/components/ui/Container';

export const metadata: Metadata = { title: 'Payment cancelled' };

interface CancelPageProps {
  searchParams: Promise<{ order?: string | string[] }>;
}

export default async function CheckoutCancelPage({ searchParams }: CancelPageProps) {
  const { order } = await searchParams;
  const reference = Array.isArray(order) ? order[0] : order;

  return (
    <Container className="py-10 md:py-14">
      <h1 className="text-3xl font-bold tracking-wide uppercase md:text-4xl">Payment cancelled</h1>
      <CancelledOrderNotice reference={reference} />
    </Container>
  );
}
