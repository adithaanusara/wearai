'use client';

import { OrderSummary } from '@/components/cart/OrderSummary';
import { ButtonLink } from '@/components/ui/ButtonLink';
import { deliveryMethods, paymentMethods } from '@/data/shipping';
import { formatPrice } from '@/lib/format';
import { readOrder } from '@/lib/order-store';
import { useHydrated } from '@/lib/use-hydrated';

export function OrderConfirmation({ reference }: { reference: string | undefined }) {
  const hydrated = useHydrated();
  if (!hydrated) return <div className="min-h-64" aria-hidden="true" />;

  const order = reference ? readOrder(reference) : null;

  if (!reference || !order) {
    return (
      <div className="mt-8 space-y-6">
        <p>
          {reference
            ? `Thank you! Your order reference is ${reference}. We could not load the details in this browser.`
            : 'We could not find an order to show.'}
        </p>
        <ButtonLink href="/">Back to the shop</ButtonLink>
      </div>
    );
  }

  const delivery = deliveryMethods.find((method) => method.id === order.deliveryMethod);
  const payment = paymentMethods.find((method) => method.id === order.paymentMethod);

  return (
    <div className="mt-8 space-y-8">
      <div className="space-y-2 text-sm">
        <p>
          Your order reference is <strong>{order.reference}</strong>.
        </p>
        <p>A confirmation will be sent to {order.email}.</p>
        {delivery && (
          <p>
            {delivery.label}: {delivery.estimate}.
          </p>
        )}
        {payment && (
          <p>
            {payment.label}. {payment.note}
          </p>
        )}
      </div>

      <div className="bg-surface max-w-md space-y-6 p-6">
        <ul className="divide-border divide-y text-sm">
          {order.lines.map((line) => (
            <li
              key={`${line.name}-${line.colour}-${line.size}`}
              className="flex justify-between gap-4 py-3 first:pt-0"
            >
              <span>
                {line.name}
                <span className="text-muted block text-xs">
                  {line.colour} · {line.size} · Qty {line.quantity}
                </span>
              </span>
              <span className="shrink-0">{formatPrice(line.total)}</span>
            </li>
          ))}
        </ul>
        <OrderSummary subtotal={order.subtotal} shipping={order.shipping} />
      </div>

      <ButtonLink href="/collections/new">Continue shopping</ButtonLink>
    </div>
  );
}
