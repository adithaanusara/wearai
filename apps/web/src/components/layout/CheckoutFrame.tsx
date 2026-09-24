import Link from 'next/link';
import type { ReactNode } from 'react';
import { Container } from '@/components/ui/Container';
import { siteConfig } from '@/config/site';

/** A distraction-free frame for checkout: no navigation, newsletter or full footer. */
export function CheckoutFrame({ children }: { children: ReactNode }) {
  return (
    <>
      <header className="border-border border-b">
        <Container className="flex h-(--header-height) items-center justify-between">
          <Link href="/" className="text-lg font-bold tracking-wide uppercase">
            {siteConfig.name}
          </Link>
          <Link href="/cart" className="text-xs font-medium tracking-wide uppercase underline">
            Back to cart
          </Link>
        </Container>
      </header>
      <main id="main" className="flex flex-1 flex-col">
        {children}
      </main>
      <footer className="border-border border-t">
        <Container className="text-muted py-6 text-xs">
          &copy; {new Date().getFullYear()} {siteConfig.name}
        </Container>
      </footer>
    </>
  );
}
