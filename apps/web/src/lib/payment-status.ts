/** What a card order's payment status means for the confirmation page. */
export type PaymentOutcome = 'confirmed' | 'pending' | 'failed';

export function paymentOutcome(status: string): PaymentOutcome {
  if (status === 'paid') return 'confirmed';
  if (status === 'failed') return 'failed';
  return 'pending'; // "unpaid" (not yet reported) or "pending" (PayHere is still processing it)
}

/** Only a card payment needs confirming here; cash on delivery and bank transfer are settled later. */
export function needsPaymentConfirmation(order: { paymentMethod: string }): boolean {
  return order.paymentMethod === 'card';
}
