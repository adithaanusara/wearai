'use client';

import { usePathname } from 'next/navigation';
import { ChatWidget } from '@/components/chat/ChatWidget';
import { CartDrawer } from '@/components/cart/CartDrawer';

/** The cart drawer and chat button belong to the shop, so they are left out of the admin area. */
export function StoreOverlays() {
  const pathname = usePathname();
  if (pathname === '/admin' || pathname.startsWith('/admin/')) return null;

  return (
    <>
      <CartDrawer />
      <ChatWidget />
    </>
  );
}
