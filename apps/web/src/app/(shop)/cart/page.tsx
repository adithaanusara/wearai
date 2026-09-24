import type { Metadata } from 'next';
import { CartView } from '@/components/cart/CartView';
import { Container } from '@/components/ui/Container';

export const metadata: Metadata = { title: 'Cart' };

export default function CartPage() {
  return (
    <Container className="py-10 md:py-14">
      <h1 className="text-3xl font-bold tracking-wide uppercase md:text-4xl">Your cart</h1>
      <CartView />
    </Container>
  );
}
