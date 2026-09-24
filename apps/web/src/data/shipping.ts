export interface DeliveryMethod {
  id: 'standard' | 'express' | 'pickup';
  label: string;
  estimate: string;
  /** Fee in whole LKR. */
  fee: number;
  /** Orders with a subtotal at or above this amount ship free. */
  freeOver?: number;
}

export const deliveryMethods: DeliveryMethod[] = [
  {
    id: 'standard',
    label: 'Standard delivery',
    estimate: '3–5 business days',
    fee: 450,
    freeOver: 15000,
  },
  { id: 'express', label: 'Express delivery', estimate: '1–2 business days', fee: 950 },
  { id: 'pickup', label: 'Store pickup', estimate: 'Ready in 1 business day', fee: 0 },
];

export interface PaymentMethod {
  id: 'cod' | 'bank-transfer' | 'card';
  label: string;
  note: string;
}

export const paymentMethods: PaymentMethod[] = [
  { id: 'cod', label: 'Cash on delivery', note: 'Pay in cash when your order arrives.' },
  {
    id: 'bank-transfer',
    label: 'Bank transfer',
    note: 'We will email our bank details. Your order ships once the payment is received.',
  },
  {
    id: 'card',
    label: 'Credit or debit card',
    note: 'You will be taken to a secure payment page after placing the order.',
  },
];
