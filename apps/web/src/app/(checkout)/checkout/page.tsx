import type { Metadata } from 'next';
import { CheckoutForm } from '@/components/checkout/CheckoutForm';
import { Container } from '@/components/ui/Container';
import { getCheckoutOptions } from '@/lib/api';

export const metadata: Metadata = { title: 'Checkout' };

// Delivery, payment and location options come from the store API, so this renders on request.
export const dynamic = 'force-dynamic';

export default async function CheckoutPage() {
  const options = await getCheckoutOptions();

  return (
    <Container className="py-10 md:py-14">
      <h1 className="text-3xl font-bold tracking-wide uppercase md:text-4xl">Checkout</h1>
      <CheckoutForm options={options} />
    </Container>
  );
}
