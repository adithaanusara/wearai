import { describe, expect, it } from 'vitest';
import {
  filterProducts,
  getFilterOptions,
  hasActiveFilters,
  parseFilters,
  sortProducts,
  type CollectionFilters,
} from '@/lib/collection';
import type { Product } from '@/types/product';

function product(overrides: Partial<Product> & Pick<Product, 'id'>): Product {
  return {
    slug: overrides.id,
    name: overrides.id,
    gender: 'women',
    category: 't-shirts',
    colour: 'Black',
    price: 3000,
    images: ['/a.svg', '/b.svg'],
    sizes: ['M'],
    isNew: false,
    ...overrides,
  };
}

const catalogue = [
  product({ id: 'a', price: 3000, colour: 'Black', sizes: ['S', 'M'] }),
  product({ id: 'b', price: 5000, colour: 'White', sizes: ['L'], isNew: true }),
  product({ id: 'c', price: 4000, colour: 'Black', sizes: ['XS', 'M'] }),
];

const noFilters: CollectionFilters = { sizes: [], colours: [], sort: 'featured' };

const ids = (products: Product[]) => products.map((item) => item.id);

describe('parseFilters', () => {
  it('reads single and repeated params', () => {
    const filters = parseFilters({ size: ['M', 'L'], colour: 'Black', min: '3500', max: '6000' });
    expect(filters).toEqual({
      sizes: ['M', 'L'],
      colours: ['Black'],
      minPrice: 3500,
      maxPrice: 6000,
      sort: 'featured',
    });
  });

  it('ignores invalid prices and unknown sort values', () => {
    const filters = parseFilters({ min: 'abc', max: '-5', sort: 'bogus' });
    expect(filters.minPrice).toBeUndefined();
    expect(filters.maxPrice).toBeUndefined();
    expect(filters.sort).toBe('featured');
  });

  it('accepts a valid sort', () => {
    expect(parseFilters({ sort: 'price-desc' }).sort).toBe('price-desc');
  });
});

describe('filterProducts', () => {
  it('returns everything when no filters are set', () => {
    expect(ids(filterProducts(catalogue, noFilters))).toEqual(['a', 'b', 'c']);
  });

  it('matches any selected size', () => {
    expect(ids(filterProducts(catalogue, { ...noFilters, sizes: ['XS', 'L'] }))).toEqual([
      'b',
      'c',
    ]);
  });

  it('combines filters with AND between groups', () => {
    const filters = { ...noFilters, sizes: ['M'], colours: ['Black'], minPrice: 3500 };
    expect(ids(filterProducts(catalogue, filters))).toEqual(['c']);
  });

  it('includes both price bounds', () => {
    const filters = { ...noFilters, minPrice: 3000, maxPrice: 4000 };
    expect(ids(filterProducts(catalogue, filters))).toEqual(['a', 'c']);
  });
});

describe('sortProducts', () => {
  it('keeps the original order for featured', () => {
    expect(ids(sortProducts(catalogue, 'featured'))).toEqual(['a', 'b', 'c']);
  });

  it('puts new products first and keeps order within groups', () => {
    expect(ids(sortProducts(catalogue, 'newest'))).toEqual(['b', 'a', 'c']);
  });

  it('sorts by price in both directions', () => {
    expect(ids(sortProducts(catalogue, 'price-asc'))).toEqual(['a', 'c', 'b']);
    expect(ids(sortProducts(catalogue, 'price-desc'))).toEqual(['b', 'c', 'a']);
  });

  it('does not change the input array', () => {
    sortProducts(catalogue, 'price-desc');
    expect(ids(catalogue)).toEqual(['a', 'b', 'c']);
  });
});

describe('getFilterOptions', () => {
  it('lists sizes in garment order, sorted colours and the price range', () => {
    expect(getFilterOptions(catalogue)).toEqual({
      sizes: ['XS', 'S', 'M', 'L'],
      colours: ['Black', 'White'],
      minPrice: 3000,
      maxPrice: 5000,
    });
  });

  it('handles an empty list', () => {
    expect(getFilterOptions([])).toEqual({ sizes: [], colours: [], minPrice: 0, maxPrice: 0 });
  });
});

describe('hasActiveFilters', () => {
  it('ignores sort but detects any real filter', () => {
    expect(hasActiveFilters({ ...noFilters, sort: 'price-asc' })).toBe(false);
    expect(hasActiveFilters({ ...noFilters, colours: ['Black'] })).toBe(true);
    expect(hasActiveFilters({ ...noFilters, minPrice: 0 })).toBe(true);
  });
});
