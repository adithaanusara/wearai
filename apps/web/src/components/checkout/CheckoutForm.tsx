'use client';

import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { useRef, useState, type FormEvent } from 'react';
import { useCart } from '@/components/cart/CartProvider';
import { OrderSummary } from '@/components/cart/OrderSummary';
import { ChoiceGroup } from '@/components/checkout/ChoiceGroup';
import { Field, SelectField } from '@/components/checkout/Field';
import { ButtonLink } from '@/components/ui/ButtonLink';
import { provinces } from '@/data/locations';
import { deliveryMethods, paymentMethods } from '@/data/shipping';
import { cartSubtotal, resolveCartLines } from '@/lib/cart';
import { validateCheckout, type CheckoutErrors, type CheckoutValues } from '@/lib/checkout';
import { formatPrice } from '@/lib/format';
import { createOrderReference, saveOrder } from '@/lib/order-store';
import { calculateShipping } from '@/lib/shipping';
import { useHydrated } from '@/lib/use-hydrated';

const initialValues: CheckoutValues = {
  email: '',
  phone: '',
  fullName: '',
  address1: '',
  address2: '',
  city: '',
  province: '',
  district: '',
  postalCode: '',
  deliveryMethod: 'standard',
  paymentMethod: 'cod',
};

// Order of the fields on the page, used to focus the first invalid one.
const fieldOrder: (keyof CheckoutValues)[] = [
  'email',
  'phone',
  'fullName',
  'address1',
  'address2',
  'city',
  'province',
  'district',
  'postalCode',
  'deliveryMethod',
  'paymentMethod',
];

const sectionTitle = 'mb-4 text-sm font-medium tracking-wide uppercase';

export function CheckoutForm() {
  const router = useRouter();
  const { items, clearCart } = useCart();
  const hydrated = useHydrated();
  const formRef = useRef<HTMLFormElement>(null);
  const [values, setValues] = useState(initialValues);
  const [errors, setErrors] = useState<CheckoutErrors>({});
  const [placing, setPlacing] = useState(false);

  const lines = resolveCartLines(items);
  const subtotal = cartSubtotal(lines);
  const shipping = calculateShipping(subtotal, values.deliveryMethod);
  const districts =
    provinces.find((province) => province.name === values.province)?.districts ?? [];

  function update(name: keyof CheckoutValues, value: string) {
    setValues((current) => ({
      ...current,
      [name]: value,
      // A district belongs to one province, so changing the province clears it.
      ...(name === 'province' ? { district: '' } : {}),
    }));
    setErrors((current) => ({ ...current, [name]: undefined }));
  }

  function onSubmit(event: FormEvent) {
    event.preventDefault();
    const found = validateCheckout(values);
    setErrors(found);

    const firstInvalid = fieldOrder.find((name) => found[name]);
    if (firstInvalid) {
      formRef.current?.querySelector<HTMLElement>(`[name="${firstInvalid}"]`)?.focus();
      return;
    }

    // Orders are not sent anywhere yet; the API replaces this in a later item.
    const reference = createOrderReference();
    saveOrder({
      reference,
      email: values.email.trim(),
      deliveryMethod: values.deliveryMethod,
      paymentMethod: values.paymentMethod,
      lines: lines.map(({ item, product, total }) => ({
        name: product.name,
        colour: product.colour,
        size: item.size,
        quantity: item.quantity,
        total,
      })),
      subtotal,
      shipping,
      total: subtotal + shipping,
    });
    setPlacing(true);
    clearCart();
    router.push(`/checkout/success?order=${reference}`);
  }

  if (!hydrated || placing) return <div className="min-h-64" aria-hidden="true" />;

  if (lines.length === 0) {
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
              value={values.email}
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
                value={values.fullName}
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
              {provinces.map((province) => (
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
            choices={deliveryMethods.map((method) => {
              const fee = calculateShipping(subtotal, method.id);
              return {
                id: method.id,
                label: method.label,
                description: method.estimate,
                detail: fee === 0 ? 'Free' : formatPrice(fee),
              };
            })}
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
            choices={paymentMethods.map((method) => ({
              id: method.id,
              label: method.label,
              description: method.note,
            }))}
          />
        </section>

        <div>
          <button
            type="submit"
            className="bg-text text-bg hover:bg-dark-2 w-full rounded-sm px-8 py-4 text-xs font-medium tracking-wide uppercase transition-colors sm:w-auto"
          >
            Place order
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
        className="bg-surface mt-10 h-fit space-y-6 p-6 lg:sticky lg:top-24 lg:mt-0"
      >
        <ul className="divide-border divide-y text-sm">
          {lines.map(({ item, product, total }) => (
            <li
              key={`${item.productId}-${item.size}`}
              className="flex justify-between gap-4 py-3 first:pt-0"
            >
              <span>
                {product.name}
                <span className="text-muted block text-xs">
                  {product.colour} · {item.size} · Qty {item.quantity}
                </span>
              </span>
              <span className="shrink-0">{formatPrice(total)}</span>
            </li>
          ))}
        </ul>
        <OrderSummary subtotal={subtotal} shipping={shipping} />
      </aside>
    </div>
  );
}
