import type { Product } from '@/types/product';

export const sortOptions = [
  { value: 'featured', label: 'Featured' },
  { value: 'newest', label: 'Newest' },
  { value: 'price-asc', label: 'Price: low to high' },
  { value: 'price-desc', label: 'Price: high to low' },
] as const;

export type SortKey = (typeof sortOptions)[number]['value'];

export interface CollectionFilters {
  sizes: string[];
  colours: string[];
  minPrice?: number;
  maxPrice?: number;
  sort: SortKey;
}

export type SearchParams = Record<string, string | string[] | undefined>;

const sizeOrder = ['XS', 'S', 'M', 'L', 'XL', 'One Size'];

function toArray(value: string | string[] | undefined): string[] {
  if (value === undefined) return [];
  return Array.isArray(value) ? value : [value];
}

function toPrice(value: string | string[] | undefined): number | undefined {
  const raw = toArray(value)[0];
  if (!raw) return undefined;
  const amount = Number(raw);
  return Number.isFinite(amount) && amount >= 0 ? amount : undefined;
}

/** Turns URL query params into typed filters, ignoring anything invalid. */
export function parseFilters(params: SearchParams): CollectionFilters {
  const sort = toArray(params.sort)[0];
  return {
    sizes: toArray(params.size),
    colours: toArray(params.colour),
    minPrice: toPrice(params.min),
    maxPrice: toPrice(params.max),
    sort: sortOptions.some((option) => option.value === sort) ? (sort as SortKey) : 'featured',
  };
}

export function filterProducts(products: Product[], filters: CollectionFilters): Product[] {
  return products.filter((product) => {
    if (filters.sizes.length && !product.sizes.some((size) => filters.sizes.includes(size))) {
      return false;
    }
    if (filters.colours.length && !filters.colours.includes(product.colour)) return false;
    if (filters.minPrice !== undefined && product.price < filters.minPrice) return false;
    if (filters.maxPrice !== undefined && product.price > filters.maxPrice) return false;
    return true;
  });
}

export function sortProducts(products: Product[], sort: SortKey): Product[] {
  const sorted = [...products];
  switch (sort) {
    case 'newest':
      // Array.sort is stable, so products keep their featured order within each group.
      return sorted.sort((a, b) => Number(b.isNew) - Number(a.isNew));
    case 'price-asc':
      return sorted.sort((a, b) => a.price - b.price);
    case 'price-desc':
      return sorted.sort((a, b) => b.price - a.price);
    default:
      return sorted;
  }
}

export interface FilterOptions {
  sizes: string[];
  colours: string[];
  minPrice: number;
  maxPrice: number;
}

/** The choices to offer, based on the products of the current collection. */
export function getFilterOptions(products: Product[]): FilterOptions {
  const sizes = [...new Set(products.flatMap((product) => product.sizes))].sort(
    (a, b) => sizeOrder.indexOf(a) - sizeOrder.indexOf(b),
  );
  const colours = [...new Set(products.map((product) => product.colour))].sort();
  const prices = products.map((product) => product.price);

  return {
    sizes,
    colours,
    minPrice: prices.length ? Math.min(...prices) : 0,
    maxPrice: prices.length ? Math.max(...prices) : 0,
  };
}

export function hasActiveFilters(filters: CollectionFilters): boolean {
  return (
    filters.sizes.length > 0 ||
    filters.colours.length > 0 ||
    filters.minPrice !== undefined ||
    filters.maxPrice !== undefined
  );
}
