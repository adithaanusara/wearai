'use client';

import { useEffect, useRef } from 'react';
import type { PayHereCheckout } from '@/types/api';

/**
 * Submits a hidden form to PayHere's checkout page, the way its API expects: the shopper's
 * browser posts these exact fields there directly, so their card details go straight to PayHere
 * and never through this site. `hash` proves the amount was set by the server, not the browser.
 */
export function PayHereRedirect({ checkout }: { checkout: PayHereCheckout }) {
  const formRef = useRef<HTMLFormElement>(null);

  useEffect(() => {
    formRef.current?.submit();
  }, []);

  const fields: Record<string, string> = {
    merchant_id: checkout.merchantId,
    return_url: checkout.returnUrl,
    cancel_url: checkout.cancelUrl,
    notify_url: checkout.notifyUrl,
    first_name: checkout.firstName,
    last_name: checkout.lastName,
    email: checkout.email,
    phone: checkout.phone,
    address: checkout.address,
    city: checkout.city,
    country: checkout.country,
    order_id: checkout.orderId,
    items: checkout.items,
    currency: checkout.currency,
    amount: checkout.amount,
    hash: checkout.hash,
  };

  return (
    <div className="mt-12 flex flex-col items-center gap-4 text-center">
      <p className="text-sm">Taking you to PayHere to pay securely…</p>
      <form ref={formRef} action={checkout.action} method="POST" className="hidden">
        {Object.entries(fields).map(([name, value]) => (
          <input key={name} type="hidden" name={name} value={value} />
        ))}
      </form>
    </div>
  );
}
