'use client';

import { CartLineItem } from '@/components/cart/CartLineItem';
import { CartNotice } from '@/components/cart/CartNotice';
import { useCart } from '@/components/cart/CartProvider';
import { CheckoutButton } from '@/components/cart/CheckoutButton';
import { useCartLines, useCartRecommendations } from '@/components/cart/useCartLines';
import { ProductCard } from '@/components/product/ProductCard';
import { ButtonLink } from '@/components/ui/ButtonLink';
import { Drawer } from '@/components/ui/Drawer';
import { canCheckout, cartSubtotal, hasCartProblems } from '@/lib/cart';
import { formatPrice } from '@/lib/format';

export function CartDrawer() {
  const { isOpen, closeCart } = useCart();
  const { lines, status, retry } = useCartLines();
  const suggestions = useCartRecommendations(lines);

  return (
    <Drawer open={isOpen} onClose={closeCart} title="Cart" side="right">
      {status === 'empty' ? (
        <div className="flex flex-1 flex-col items-center justify-center gap-6 p-(--gutter) text-center">
          <p className="text-sm">Your cart is empty.</p>
          <ButtonLink href="/collections/new" variant="primary" onClick={closeCart}>
            Continue shopping
          </ButtonLink>
        </div>
      ) : (
        <>
          <div className="flex-1 overflow-y-auto px-(--gutter)">
            <CartNotice status={status} hasProblems={hasCartProblems(lines)} onRetry={retry} />
            <ul className="divide-border divide-y">
              {lines.map((line) => (
                <CartLineItem key={`${line.item.productId}-${line.item.size}`} line={line} />
              ))}
            </ul>

            {status === 'ready' && suggestions.length > 0 && (
              <section aria-labelledby="cart-suggestions" className="border-border border-t py-6">
                <h3
                  id="cart-suggestions"
                  className="mb-4 text-xs font-medium tracking-wide uppercase"
                >
                  You may also like
                </h3>
                <ul className="grid grid-cols-2 gap-4">
                  {suggestions.map((product) => (
                    <li key={product.id}>
                      <ProductCard product={product} imageSizes="180px" />
                    </li>
                  ))}
                </ul>
              </section>
            )}
          </div>

          <div className="border-border space-y-4 border-t p-(--gutter)">
            {status === 'ready' && (
              <p className="flex items-center justify-between text-sm font-medium">
                <span>Subtotal</span>
                <span>{formatPrice(cartSubtotal(lines))}</span>
              </p>
            )}
            <p className="text-muted text-xs">Tax included. Shipping calculated at checkout.</p>
            <div className="grid grid-cols-2 gap-3">
              <ButtonLink href="/cart" variant="secondary" onClick={closeCart}>
                View cart
              </ButtonLink>
              <CheckoutButton enabled={canCheckout(lines)} onNavigate={closeCart} />
            </div>
          </div>
        </>
      )}
    </Drawer>
  );
}
