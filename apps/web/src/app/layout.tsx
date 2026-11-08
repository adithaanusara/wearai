import type { Metadata } from 'next';
import { Inter } from 'next/font/google';
import { siteConfig } from '@/config/site';
import { QueryProvider } from '@/components/providers';
import { CartProvider } from '@/components/cart/CartProvider';
import { SkipLink } from '@/components/layout/SkipLink';
import { StoreOverlays } from '@/components/layout/StoreOverlays';
import './globals.css';

const inter = Inter({
  variable: '--font-inter',
  subsets: ['latin'],
});

// Render pages in Singapore, next to the API (Render, Singapore). Each page makes several API
// calls, and from Vercel's default region (Washington, D.C.) every one of them crossed the Pacific.
// Every page and route below this layout inherits it.
export const preferredRegion = 'sin1';

export const metadata: Metadata = {
  title: siteConfig.name,
  description: siteConfig.description,
};

export default function RootLayout({ children }: LayoutProps<'/'>) {
  return (
    <html lang="en" className={`${inter.variable} h-full antialiased`}>
      <body className="flex min-h-full flex-col">
        <QueryProvider>
          <CartProvider>
            <SkipLink />
            {children}
            <StoreOverlays />
          </CartProvider>
        </QueryProvider>
      </body>
    </html>
  );
}
