import type { Metadata } from 'next';
import { Inter } from 'next/font/google';
import { siteConfig } from '@/config/site';
import { CartDrawer } from '@/components/cart/CartDrawer';
import { CartProvider } from '@/components/cart/CartProvider';
import { SkipLink } from '@/components/layout/SkipLink';
import './globals.css';

const inter = Inter({
  variable: '--font-inter',
  subsets: ['latin'],
});

export const metadata: Metadata = {
  title: siteConfig.name,
  description: siteConfig.description,
};

export default function RootLayout({ children }: LayoutProps<'/'>) {
  return (
    <html lang="en" className={`${inter.variable} h-full antialiased`}>
      <body className="flex min-h-full flex-col">
        <CartProvider>
          <SkipLink />
          {children}
          <CartDrawer />
        </CartProvider>
      </body>
    </html>
  );
}
