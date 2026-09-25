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

// Empty values such as `?size=` are dropped: an empty filter would otherwise match nothing.
function toArray(value: string | string[] | undefined): string[] {
  if (value === undefined) return [];
  return (Array.isArray(value) ? value : [value]).filter((item) => item !== '');
}

function toPrice(value: string | string[] | undefined): number | undefined {
  const raw = toArray(value)[0];
  if (!raw) return undefined;
  const amount = Number(raw);
  // The API takes whole rupees, so anything else is ignored.
  return Number.isInteger(amount) && amount >= 0 ? amount : undefined;
}

/**
 * Turns URL query params into typed filters. The API is strict about bad values, but a
 * hand-edited URL should still give a page, so anything invalid is ignored here first.
 */
export function parseFilters(params: SearchParams): CollectionFilters {
  const sort = toArray(params.sort)[0];
  let minPrice = toPrice(params.min);
  let maxPrice = toPrice(params.max);
  // A reversed range is taken to mean the other way round.
  if (minPrice !== undefined && maxPrice !== undefined && minPrice > maxPrice) {
    [minPrice, maxPrice] = [maxPrice, minPrice];
  }

  return {
    sizes: toArray(params.size),
    colours: toArray(params.colour),
    minPrice,
    maxPrice,
    sort: sortOptions.some((option) => option.value === sort) ? (sort as SortKey) : 'featured',
  };
}

/** The page number from the URL: a whole number from 1, otherwise 1. */
export function parsePage(params: SearchParams): number {
  const page = Number(toArray(params.page)[0]);
  return Number.isInteger(page) && page >= 1 ? page : 1;
}

export function hasActiveFilters(filters: CollectionFilters): boolean {
  return (
    filters.sizes.length > 0 ||
    filters.colours.length > 0 ||
    filters.minPrice !== undefined ||
    filters.maxPrice !== undefined
  );
}

/** The parameters are named the same in the page URL and in the API, so this serves both. */
export function toQuery(filters: CollectionFilters, page = 1, pageSize?: number) {
  return {
    size: filters.sizes,
    colour: filters.colours,
    min: filters.minPrice,
    max: filters.maxPrice,
    sort: filters.sort === 'featured' ? undefined : filters.sort,
    page: page > 1 ? page : undefined,
    pageSize,
  };
}
