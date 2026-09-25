'use client';

import { useQuery } from '@tanstack/react-query';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { useRef, useState, type FormEvent } from 'react';
import { useSession } from '@/components/account/useSession';
import { useCart } from '@/components/cart/CartProvider';
import { OrderSummary } from '@/components/cart/OrderSummary';
import { ChoiceGroup } from '@/components/checkout/ChoiceGroup';
import { ButtonLink } from '@/components/ui/ButtonLink';
import { Field, SelectField } from '@/components/ui/Field';
import { ApiError, placeOrder, quoteCart } from '@/lib/api';
import {
  firstInvalidField,
  initialValues,
  mapProblems,
  type CheckoutErrors,
  type CheckoutValues,
} from '@/lib/checkout-form';
import { formatPrice } from '@/lib/format';
import { clearCheckoutKey, getCheckoutKey } from '@/lib/idempotency';
import { saveOrder } from '@/lib/order-store';
import { useHydrated } from '@/lib/use-hydrated';
import type { CheckoutOptions } from '@/types/api';

const sectionTitle = 'mb-4 text-sm font-medium tracking-wide uppercase';

const cartProblemMessage = 'Some items in your cart can no longer be ordered.';
const conflictMessage =
  'An earlier attempt to place this order used different details. Please check them and place the order again.';
const unreachableMessage =
  'We could not reach the store. Your cart is safe. Please try again in a moment.';

export function CheckoutForm({ options }: { options: CheckoutOptions }) {
  const router = useRouter();
  const { items, clearCart } = useCart();
  const hydrated = useHydrated();
  const { session } = useSession();
  const formRef = useRef<HTMLFormElement>(null);
  // A ref, not state: a fast double click fires twice before a state update can disable the button.
  const submitting = useRef(false);

  const [values, setValues] = useState(initialValues);
  // Fields the shopper has edited. The others may be pre-filled from their account.
  const [touched, setTouched] = useState<Set<keyof CheckoutValues>>(() => new Set());
  const [errors, setErrors] = useState<CheckoutErrors>({});
  const [banner, setBanner] = useState<{ text: string; cartLink?: boolean } | null>(null);
  const [busy, setBusy] = useState(false);
  const [placed, setPlaced] = useState(false);

  // The server prices the cart. The numbers on this page are its answer, never our own arithmetic.
  const quote = useQuery({
    queryKey: ['quote', items, values.deliveryMethod],
    queryFn: () => quoteCart(items, values.deliveryMethod),
    enabled: hydrated && items.length > 0 && !placed,
    retry: (failures, error) => !(error instanceof ApiError && error.status < 500) && failures < 1,
  });
  const cartRejected = quote.error instanceof ApiError && quote.error.status === 422;

  const shown: CheckoutValues = {
    ...values,
    email: touched.has('email') ? values.email : (session?.email ?? values.email),
    fullName: touched.has('fullName') ? values.fullName : (session?.name ?? values.fullName),
  };

  const districts =
    options.provinces.find((province) => province.name === values.province)?.districts ?? [];

  function update(name: keyof CheckoutValues, value: string) {
    setTouched((current) => new Set(current).add(name));
    setValues((current) => ({
      ...current,
      [name]: value,
      // A district belongs to one province, so changing the province clears it.
      ...(name === 'province' ? { district: '' } : {}),
    }));
    setErrors((current) => ({ ...current, [name]: undefined }));
  }

  function showProblems(error: unknown) {
    if (error instanceof ApiError && error.status === 422) {
      const { fields, cartProblem, other } = mapProblems(error.problems);
      setErrors(fields);
      const first = firstInvalidField(fields);
      if (first) formRef.current?.querySelector<HTMLElement>(`[name="${first}"]`)?.focus();
      if (cartProblem) setBanner({ text: cartProblemMessage, cartLink: true });
      else if (other) setBanner({ text: other });
      return;
    }
    if (error instanceof ApiError && error.status === 409) {
      // The key was used for different details, so the next attempt needs a fresh one.
      clearCheckoutKey();
      setBanner({ text: conflictMessage });
      return;
    }
    // Anything else (network, server error): the same key is kept, so a retry cannot double-order.
    setBanner({
      text: error instanceof ApiError && error.status < 500 ? error.message : unreachableMessage,
    });
  }

  async function onSubmit(event: FormEvent) {
    event.preventDefault();
    if (submitting.current) return;
    submitting.current = true;
    setBusy(true);
    setBanner(null);
    setErrors({});

    try {
      const order = await placeOrder({ ...shown, items }, getCheckoutKey());
      // The cart is cleared only now that the server has confirmed the order.
      saveOrder(order);
      clearCheckoutKey();
      setPlaced(true);
      clearCart();
      router.push(`/checkout/success?order=${encodeURIComponent(order.reference)}`);
    } catch (error) {
      showProblems(error);
    } finally {
      submitting.current = false;
      setBusy(false);
    }
  }

  if (!hydrated || placed) return <div className="min-h-64" aria-hidden="true" />;

  if (items.length === 0) {
    return (
      <div className="mt-12 flex flex-col items-center gap-6 text-center">
        <p>Your cart is empty.</p>
        <ButtonLink href="/collections/new">Continue shopping</ButtonLink>
      </div>
    );
  }

  return (
    <div className="mt-8 gap-12 lg:grid lg:grid-cols-[1fr_24rem]">
      <form ref={formRef} onSubmit={onSubmit} noValidate className="space-y-10">
        {(banner || cartRejected) && (
          <div role="alert" className="border-error text-error rounded-sm border p-4 text-sm">
            {banner?.text ?? cartProblemMessage}{' '}
            {(banner?.cartLink || cartRejected) && (
              <Link href="/cart" className="underline">
                Review your cart
              </Link>
            )}
          </div>
        )}

        <section aria-labelledby="contact-title">
          <h2 id="contact-title" className={sectionTitle}>
            Contact
          </h2>
          <div className="grid gap-4 sm:grid-cols-2">
            <Field
              name="email"
              label="Email"
              type="email"
              autoComplete="email"
              value={shown.email}
              error={errors.email}
              onChange={(event) => update('email', event.target.value)}
            />
            <Field
              name="phone"
              label="Mobile number"
              type="tel"
              autoComplete="tel"
              placeholder="077 123 4567"
              value={values.phone}
              error={errors.phone}
              onChange={(event) => update('phone', event.target.value)}
            />
          </div>
        </section>

        <section aria-labelledby="delivery-title">
          <h2 id="delivery-title" className={sectionTitle}>
            Delivery address
          </h2>
          <div className="grid gap-4 sm:grid-cols-2">
            <div className="sm:col-span-2">
              <Field
                name="fullName"
                label="Full name"
                autoComplete="name"
                value={shown.fullName}
                error={errors.fullName}
                onChange={(event) => update('fullName', event.target.value)}
              />
            </div>
            <div className="sm:col-span-2">
              <Field
                name="address1"
                label="Address"
                autoComplete="address-line1"
                value={values.address1}
                error={errors.address1}
                onChange={(event) => update('address1', event.target.value)}
              />
            </div>
            <div className="sm:col-span-2">
              <Field
                name="address2"
                label="Apartment, suite, etc. (optional)"
                autoComplete="address-line2"
                value={values.address2}
                error={errors.address2}
                onChange={(event) => update('address2', event.target.value)}
              />
            </div>
            <Field
              name="city"
              label="City"
              autoComplete="address-level2"
              value={values.city}
              error={errors.city}
              onChange={(event) => update('city', event.target.value)}
            />
            <Field
              name="postalCode"
              label="Postal code"
              inputMode="numeric"
              autoComplete="postal-code"
              value={values.postalCode}
              error={errors.postalCode}
              onChange={(event) => update('postalCode', event.target.value)}
            />
            <SelectField
              name="province"
              label="Province"
              value={values.province}
              error={errors.province}
              onChange={(event) => update('province', event.target.value)}
            >
              <option value="">Select a province</option>
              {options.provinces.map((province) => (
                <option key={province.name} value={province.name}>
                  {province.name}
                </option>
              ))}
            </SelectField>
            <SelectField
              name="district"
              label="District"
              value={values.district}
              error={errors.district}
              disabled={!values.province}
              onChange={(event) => update('district', event.target.value)}
            >
              <option value="">Select a district</option>
              {districts.map((district) => (
                <option key={district} value={district}>
                  {district}
                </option>
              ))}
            </SelectField>
          </div>
        </section>

        <section aria-labelledby="shipping-title">
          <h2 id="shipping-title" className={sectionTitle}>
            Delivery method
          </h2>
          <ChoiceGroup
            name="deliveryMethod"
            legend="Choose how you want to receive your order"
            value={values.deliveryMethod}
            error={errors.deliveryMethod}
            onChange={(value) => update('deliveryMethod', value)}
            choices={options.deliveryMethods.map((method) => ({
              id: method.id,
              label: method.label,
              description:
                method.freeOver === null
                  ? method.estimate
                  : `${method.estimate} · Free over ${formatPrice(method.freeOver)}`,
              detail: method.fee === 0 ? 'Free' : formatPrice(method.fee),
            }))}
          />
        </section>

        <section aria-labelledby="payment-title">
          <h2 id="payment-title" className={sectionTitle}>
            Payment
          </h2>
          <ChoiceGroup
            name="paymentMethod"
            legend="Choose how you want to pay"
            value={values.paymentMethod}
            error={errors.paymentMethod}
            onChange={(value) => update('paymentMethod', value)}
            choices={options.paymentMethods.map((method) => ({
              id: method.id,
              label: method.label,
              description: method.note,
            }))}
          />
        </section>

        <div>
          <button
            type="submit"
            disabled={busy || !quote.data}
            className="bg-text text-bg hover:bg-dark-2 w-full rounded-sm px-8 py-4 text-xs font-medium tracking-wide uppercase transition-colors disabled:opacity-40 sm:w-auto"
          >
            {busy ? 'Placing order…' : 'Place order'}
          </button>
          <p className="text-muted mt-3 text-xs">
            By placing your order you agree to our{' '}
            <Link href="/returns" className="underline">
              returns policy
            </Link>
            .
          </p>
        </div>
      </form>

      <aside
        aria-label="Order summary"
        aria-busy={quote.isPending}
        className="bg-surface mt-10 h-fit space-y-6 p-6 lg:sticky lg:top-24 lg:mt-0"
      >
        {quote.data ? (
          <>
            <ul className="divide-border divide-y text-sm">
              {quote.data.lines.map((line) => (
                <li
                  key={`${line.productId}-${line.size}`}
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
            <OrderSummary subtotal={quote.data.subtotal} shipping={quote.data.shipping} />
          </>
        ) : quote.isError && !cartRejected ? (
          <div className="space-y-3 text-sm" role="alert">
            <p>We could not work out your total.</p>
            <button type="button" className="underline" onClick={() => void quote.refetch()}>
              Try again
            </button>
          </div>
        ) : cartRejected ? (
          <p className="text-sm">Your total appears once the cart can be ordered.</p>
        ) : (
          <p className="text-muted text-sm">Calculating your total…</p>
        )}
      </aside>
    </div>
  );
}
