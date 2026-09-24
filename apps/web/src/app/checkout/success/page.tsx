import type { Metadata } from 'next';
import { OrderConfirmation } from '@/components/checkout/OrderConfirmation';
import { Container } from '@/components/ui/Container';

export const metadata: Metadata = { title: 'Order confirmed' };

interface SuccessPageProps {
  searchParams: Promise<{ order?: string | string[] }>;
}

export default async function CheckoutSuccessPage({ searchParams }: SuccessPageProps) {
  const { order } = await searchParams;
  const reference = Array.isArray(order) ? order[0] : order;

  return (
    <Container className="py-10 md:py-14">
      <h1 className="text-3xl font-bold tracking-wide uppercase md:text-4xl">Thank you</h1>
      <OrderConfirmation reference={reference} />
    </Container>
  );
}
