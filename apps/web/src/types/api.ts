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

export interface Order extends Quote {
  reference: string;
  status: string;
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

export interface User {
  id: number;
  name: string;
  email: string;
}
