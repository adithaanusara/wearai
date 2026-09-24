import { deliveryMethods } from '@/data/shipping';

/** Shipping fee in whole LKR for a subtotal and delivery method. Unknown methods cost nothing. */
export function calculateShipping(subtotal: number, methodId: string): number {
  const method = deliveryMethods.find((candidate) => candidate.id === methodId);
  if (!method) return 0;
  if (method.freeOver !== undefined && subtotal >= method.freeOver) return 0;
  return method.fee;
}
