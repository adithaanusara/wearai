'use client';

import { useQuery } from '@tanstack/react-query';
import { useEffect, useState } from 'react';
import { OrderSummary } from '@/components/cart/OrderSummary';
import { ButtonLink } from '@/components/ui/ButtonLink';
import { getOrderStatus } from '@/lib/api';
import { formatPrice } from '@/lib/format';
import { readOrder } from '@/lib/order-store';
import { needsPaymentConfirmation, paymentOutcome } from '@/lib/payment-status';
import { useHydrated } from '@/lib/use-hydrated';
import type { CheckoutOptions } from '@/types/api';

interface OrderConfirmationProps {
  reference: string | undefined;
  /** Used to describe the delivery and payment choices. Null when the API could not be reached. */
  options: CheckoutOptions | null;
}

const POLL_INTERVAL_MS = 2000;
const MAX_WAIT_MS = 30_000; // then the page stops guessing and says so
const MAX_POLLS = Math.ceil(MAX_WAIT_MS / POLL_INTERVAL_MS);

export function OrderConfirmation({ reference, options }: OrderConfirmationProps) {
  const hydrated = useHydrated();
  const order = hydrated && reference ? readOrder(reference) : null;
  const awaitingPayment = order !== null && needsPaymentConfirmation(order);
  // A plain timer, not a poll count: it fires once, on its own, and only then sets state - the
  // pattern for subscribing to an external timer that this project's linting rules ask for.
  const [timedOut, setTimedOut] = useState(false);
  useEffect(() => {
    if (!awaitingPayment) return;
    const timer = setTimeout(() => setTimedOut(true), MAX_WAIT_MS);
    return () => clearTimeout(timer);
  }, [awaitingPayment]);

  // PayHere confirms the payment separately from the browser's own redirect back to this page, so
  // this page asks the server rather than assuming the redirect alone means the shopper paid. The
  // query stops itself after MAX_POLLS fetches, and also as soon as the status resolves either way.
  const status = useQuery({
    queryKey: ['order-status', reference],
    queryFn: () => getOrderStatus(reference as string),
    enabled: awaitingPayment,
    refetchInterval: (query) => {
      if (query.state.dataUpdateCount >= MAX_POLLS) return false;
      const outcome = query.state.data ? paymentOutcome(query.state.data.paymentStatus) : 'pending';
      return outcome === 'pending' ? POLL_INTERVAL_MS : false;
    },
    refetchOnWindowFocus: false,
  });

  if (!hydrated) return <div className="min-h-64" aria-hidden="true" />;

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

  const outcome = awaitingPayment
    ? paymentOutcome(status.data?.paymentStatus ?? 'unpaid')
    : 'confirmed';

  if (awaitingPayment && outcome === 'pending' && !timedOut) {
    return (
      <div className="mt-12 flex flex-col items-center gap-3 text-center">
        <p>Confirming your payment…</p>
        <p className="text-muted text-sm">Order reference: {order.reference}</p>
      </div>
    );
  }

  if (outcome === 'failed') {
    return (
      <div className="mt-8 space-y-6">
        <p role="alert">
          Your order (reference {order.reference}) was placed, but the payment did not go through.
        </p>
        <p className="text-sm">Please try again, or choose a different payment method.</p>
        <ButtonLink href="/cart">Back to your cart</ButtonLink>
      </div>
    );
  }

  const delivery = options?.deliveryMethods.find((method) => method.id === order.deliveryMethod);
  const payment = options?.paymentMethods.find((method) => method.id === order.paymentMethod);

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
            {payment.label}.{' '}
            {awaitingPayment
              ? outcome === 'confirmed'
                ? 'Payment received.'
                : 'Payment not yet confirmed.'
              : payment.note}
          </p>
        )}
        {timedOut && (
          <p className="text-muted">
            We have not heard back from the payment provider yet. This page will not update further,
            but your order is saved; check your account or email for confirmation.
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
              <span className="shrink-0">{formatPrice(line.lineTotal)}</span>
            </li>
          ))}
        </ul>
        <OrderSummary subtotal={order.subtotal} shipping={order.shipping} />
      </div>

      <ButtonLink href="/collections/new">Continue shopping</ButtonLink>
    </div>
  );
}
