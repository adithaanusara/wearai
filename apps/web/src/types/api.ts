import type { Product } from '@/types/product';

/** Shapes returned by the store API (camelCase JSON). Products use the shared Product type. */

export interface Page<T> {
  items: T[];
  total: number;
  page: number;
  pageSize: number;
}

export interface FilterOptions {
  sizes: string[];
  colours: string[];
  minPrice: number;
  maxPrice: number;
}

export interface CollectionPage extends Page<Product> {
  slug: string;
  title: string;
  filterOptions: FilterOptions;
}

export interface ProductDetail extends Product {
  colourways: { id: string; slug: string; colour: string }[];
  rating: { average: number | null; count: number };
}

export interface Review {
  id: string;
  /** A review applies to every colour of a style. */
  styleId: string;
  rating: number;
  title: string;
  body: string;
  author: string;
  /** ISO date, e.g. 2026-09-12. */
  date: string;
}

export interface CheckoutOptions {
  deliveryMethods: {
    id: string;
    label: string;
    estimate: string;
    fee: number;
    /** Orders at or above this subtotal ship free. */
    freeOver: number | null;
  }[];
  paymentMethods: { id: string; label: string; note: string }[];
  provinces: { name: string; districts: string[] }[];
}

export interface OrderLine {
  productId: string;
  name: string;
  colour: string;
  size: string;
  unitPrice: number;
  quantity: number;
  lineTotal: number;
}

/** The server's price for a cart. Amounts are whole LKR. */
export interface Quote {
  lines: OrderLine[];
  subtotal: number;
  shipping: number;
  total: number;
}

export interface PayHereCheckout {
  action: string;
  merchantId: string;
  orderId: string;
  items: string;
  amount: string;
  currency: string;
  hash: string;
  firstName: string;
  lastName: string;
  email: string;
  phone: string;
  address: string;
  city: string;
  country: string;
  returnUrl: string;
  cancelUrl: string;
  notifyUrl: string;
}

export interface OrderStatus {
  status: string;
  paymentStatus: string;
}

export interface Order extends Quote {
  reference: string;
  status: string;
  paymentStatus: string;
  /** Present only on the response to placing a card order, and only once. */
  payhere: PayHereCheckout | null;
  email: string;
  phone: string;
  fullName: string;
  address1: string;
  address2: string;
  city: string;
  province: string;
  district: string;
  postalCode: string;
  deliveryMethod: string;
  paymentMethod: string;
  createdAt: string;
}

/** What the checkout form sends. Prices are never included: the server works them out. */
export interface OrderRequest {
  items: { productId: string; size: string; quantity: number }[];
  deliveryMethod: string;
  paymentMethod: string;
  email: string;
  phone: string;
  fullName: string;
  address1: string;
  address2: string;
  city: string;
  province: string;
  district: string;
  postalCode: string;
  /** The total the shopper was shown. The server only compares it; it never sets a price. */
  expectedTotal?: number;
}

export type Role = 'customer' | 'staff' | 'admin';

export interface User {
  id: number;
  name: string;
  email: string;
  role: Role;
  twoFactorEnabled: boolean;
}

/** What /auth/login returns instead of a user when the password was right but a code is still
 * needed. There is no session yet. */
export interface TwoFactorRequired {
  twoFactorRequired: true;
  pendingToken: string;
}

export type LoginResult = User | TwoFactorRequired;

export function needsTwoFactor(result: LoginResult): result is TwoFactorRequired {
  return 'twoFactorRequired' in result;
}

export interface TwoFactorSetup {
  secret: string;
  provisioningUri: string;
}

/** A user as an admin sees them in the users list. */
export interface AdminUser extends User {
  createdAt: string;
}

export interface AuditEntry {
  id: number;
  createdAt: string;
  actorEmail: string;
  action: string;
  entity: string;
  entityId: string;
  details: Record<string, unknown>;
}

export interface Dashboard {
  ordersByStatus: Record<string, number>;
  products: number;
  customers: number;
}

export interface OrderSummary {
  reference: string;
  status: string;
  paymentStatus: string;
  email: string;
  fullName: string;
  total: number;
  createdAt: string;
}

export interface StatusChange {
  fromStatus: string;
  toStatus: string;
  actorEmail: string;
  createdAt: string;
}

export interface PaymentEvent {
  fromStatus: string;
  toStatus: string;
  source: string;
  method: string | null;
  message: string | null;
  createdAt: string;
}

/** An order as staff see it: the customer's order plus its history and the moves allowed now. */
export interface AdminOrder extends Order {
  history: StatusChange[];
  allowedNext: string[];
  paymentEvents: PaymentEvent[];
}

export interface AdminProduct {
  id: string;
  slug: string;
  name: string;
  colour: string;
  gender: string;
  category: string;
  price: number;
  compareAtPrice: number | null;
  description: string;
  images: { id: number; url: string }[];
  sizes: string[];
  archived: boolean;
  /** The version of the product. An edit sends it back, so a stale screen is refused. */
  updatedAt: string;
}
