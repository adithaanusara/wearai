'use client';

import {
  createContext,
  useCallback,
  useContext,
  useMemo,
  useState,
  useSyncExternalStore,
  type ReactNode,
} from 'react';
import { cartCount } from '@/lib/cart';
import {
  dispatchCart,
  getCartSnapshot,
  getServerCartSnapshot,
  subscribeToCart,
} from '@/lib/cart-store';
import type { CartItem } from '@/types/cart';

interface CartContextValue {
  items: CartItem[];
  count: number;
  isOpen: boolean;
  openCart: () => void;
  closeCart: () => void;
  addItem: (productId: string, size: string) => void;
  removeItem: (productId: string, size: string) => void;
  setQuantity: (productId: string, size: string, quantity: number) => void;
}

const CartContext = createContext<CartContextValue | null>(null);

export function CartProvider({ children }: { children: ReactNode }) {
  const items = useSyncExternalStore(subscribeToCart, getCartSnapshot, getServerCartSnapshot);
  const [isOpen, setIsOpen] = useState(false);

  const openCart = useCallback(() => setIsOpen(true), []);
  const closeCart = useCallback(() => setIsOpen(false), []);

  const value = useMemo<CartContextValue>(
    () => ({
      items,
      count: cartCount(items),
      isOpen,
      openCart,
      closeCart,
      addItem: (productId, size) => dispatchCart({ type: 'add', productId, size }),
      removeItem: (productId, size) => dispatchCart({ type: 'remove', productId, size }),
      setQuantity: (productId, size, quantity) =>
        dispatchCart({ type: 'setQuantity', productId, size, quantity }),
    }),
    [items, isOpen, openCart, closeCart],
  );

  return <CartContext.Provider value={value}>{children}</CartContext.Provider>;
}

export function useCart(): CartContextValue {
  const context = useContext(CartContext);
  if (!context) throw new Error('useCart must be used inside CartProvider');
  return context;
}
