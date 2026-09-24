import type { Metadata } from 'next';
import { CheckoutForm } from '@/components/checkout/CheckoutForm';
import { Container } from '@/components/ui/Container';

export const metadata: Metadata = { title: 'Checkout' };

export default function CheckoutPage() {
  return (
    <Container className="py-10 md:py-14">
      <h1 className="text-3xl font-bold tracking-wide uppercase md:text-4xl">Checkout</h1>
      <CheckoutForm />
    </Container>
  );
}
