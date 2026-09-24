import type { ReactNode } from 'react';
import { CheckoutFrame } from '@/components/layout/CheckoutFrame';

export default function CheckoutLayout({ children }: { children: ReactNode }) {
  return <CheckoutFrame>{children}</CheckoutFrame>;
}
