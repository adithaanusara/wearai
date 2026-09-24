import type { Metadata } from 'next';
import { ShopShell } from '@/components/layout/ShopShell';
import { ButtonLink } from '@/components/ui/ButtonLink';
import { Container } from '@/components/ui/Container';

export const metadata: Metadata = { title: 'Page not found' };

// Unknown URLs and notFound() calls are rendered here, outside the route groups, so the frame is added by hand.
export default function NotFound() {
  return (
    <ShopShell>
      <Container className="flex flex-1 flex-col items-center justify-center gap-6 py-24 text-center">
        <h1 className="text-3xl font-bold tracking-wide uppercase">Page not found</h1>
        <p className="text-muted text-sm">The page you are looking for does not exist.</p>
        <ButtonLink href="/">Back to the shop</ButtonLink>
      </Container>
    </ShopShell>
  );
}
