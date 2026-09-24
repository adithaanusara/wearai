export interface AccountOrder {
  reference: string;
  /** ISO date, e.g. 2026-09-12. */
  date: string;
  status: 'Processing' | 'Shipped' | 'Delivered';
  items: string[];
  /** Order total in whole LKR. */
  total: number;
}

// Sample orders for the demo account page; the API supplies real ones later.
export const mockOrders: AccountOrder[] = [
  {
    reference: 'WA-1042',
    date: '2026-09-12',
    status: 'Processing',
    items: ['Seamless High-Rise Leggings (M) × 1', 'Everyday Cap × 1'],
    total: 9350,
  },
  {
    reference: 'WA-0987',
    date: '2026-08-21',
    status: 'Delivered',
    items: ['Pullover Hoodie (L) × 1'],
    total: 9900,
  },
  {
    reference: 'WA-0913',
    date: '2026-07-30',
    status: 'Delivered',
    items: ['Essential Fitted Tee (S) × 2', 'Training Shorts (S) × 1'],
    total: 10450,
  },
];
