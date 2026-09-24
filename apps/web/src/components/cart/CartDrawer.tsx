'use client';

import { CartLineItem } from '@/components/cart/CartLineItem';
import { useCart } from '@/components/cart/CartProvider';
import { ProductCard } from '@/components/product/ProductCard';
import { ButtonLink } from '@/components/ui/ButtonLink';
import { Drawer } from '@/components/ui/Drawer';
import { cartSubtotal, getCartRecommendations, resolveCartLines } from '@/lib/cart';
import { formatPrice } from '@/lib/format';

export function CartDrawer() {
  const { items, isOpen, closeCart } = useCart();
  const lines = resolveCartLines(items);
  const suggestions = getCartRecommendations(lines);

  return (
    <Drawer open={isOpen} onClose={closeCart} title="Cart" side="right">
      {lines.length === 0 ? (
        <div className="flex flex-1 flex-col items-center justify-center gap-6 p-(--gutter) text-center">
          <p className="text-sm">Your cart is empty.</p>
          <ButtonLink href="/collections/new" variant="primary" onClick={closeCart}>
            Continue shopping
          </ButtonLink>
        </div>
      ) : (
        <>
          <div className="flex-1 overflow-y-auto px-(--gutter)">
            <ul className="divide-border divide-y">
              {lines.map((line) => (
                <CartLineItem key={`${line.item.productId}-${line.item.size}`} line={line} />
              ))}
            </ul>

            {suggestions.length > 0 && (
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
            <p className="flex items-center justify-between text-sm font-medium">
              <span>Subtotal</span>
              <span>{formatPrice(cartSubtotal(lines))}</span>
            </p>
            <p className="text-muted text-xs">Tax included. Shipping calculated at checkout.</p>
            <div className="grid grid-cols-2 gap-3">
              <ButtonLink href="/cart" variant="secondary" onClick={closeCart}>
                View cart
              </ButtonLink>
              <ButtonLink href="/checkout" variant="primary" onClick={closeCart}>
                Checkout
              </ButtonLink>
            </div>
          </div>
        </>
      )}
    </Drawer>
  );
}
