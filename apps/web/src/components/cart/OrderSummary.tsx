import { formatPrice } from '@/lib/format';

interface OrderSummaryProps {
  subtotal: number;
  /** Shipping in whole LKR, or null while it is not known yet. */
  shipping: number | null;
}

export function OrderSummary({ subtotal, shipping }: OrderSummaryProps) {
  return (
    <dl className="space-y-3 text-sm">
      <div className="flex justify-between">
        <dt>Subtotal</dt>
        <dd>{formatPrice(subtotal)}</dd>
      </div>
      <div className="flex justify-between">
        <dt>Shipping</dt>
        <dd>
          {shipping === null
            ? 'Calculated at checkout'
            : shipping === 0
              ? 'Free'
              : formatPrice(shipping)}
        </dd>
      </div>
      {shipping !== null && (
        <div className="border-border flex justify-between border-t pt-3 text-base font-medium">
          <dt>Total</dt>
          <dd>{formatPrice(subtotal + shipping)}</dd>
        </div>
      )}
      <p className="text-muted pt-1 text-xs">Tax included.</p>
    </dl>
  );
}
