import type { ReactNode } from 'react';
import { Footer } from '@/components/layout/Footer';
import { Header } from '@/components/layout/Header';
import { NewsletterSection } from '@/components/layout/NewsletterSection';

/** The full site frame: header, page content, newsletter and footer. */
export function ShopShell({ children }: { children: ReactNode }) {
  return (
    <>
      <Header />
      <main id="main" className="flex flex-1 flex-col">
        {children}
      </main>
      <NewsletterSection />
      <Footer />
    </>
  );
}
