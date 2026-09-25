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
