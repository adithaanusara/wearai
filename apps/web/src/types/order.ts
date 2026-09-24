export interface PlacedOrderLine {
  name: string;
  colour: string;
  size: string;
  quantity: number;
  /** Line total in whole LKR. */
  total: number;
}

export interface PlacedOrder {
  reference: string;
  email: string;
  deliveryMethod: string;
  paymentMethod: string;
  lines: PlacedOrderLine[];
  subtotal: number;
  shipping: number;
  total: number;
}
