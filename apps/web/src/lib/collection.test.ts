import { describe, expect, it } from 'vitest';
import { buildQuery } from '@/lib/api';
import {
  hasActiveFilters,
  parseFilters,
  parsePage,
  toQuery,
  type CollectionFilters,
} from '@/lib/collection';

const noFilters: CollectionFilters = { sizes: [], colours: [], sort: 'featured' };

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

  it('ignores prices the API would reject: decimals and values that are not numbers', () => {
    expect(parseFilters({ min: '3500.5' }).minPrice).toBeUndefined();
    expect(parseFilters({ max: 'Infinity' }).maxPrice).toBeUndefined();
    expect(parseFilters({ min: '1e3' }).minPrice).toBe(1000);
  });

  it('keeps zero as a real price', () => {
    expect(parseFilters({ min: '0' }).minPrice).toBe(0);
  });

  it('swaps a reversed price range', () => {
    const filters = parseFilters({ min: '6000', max: '3000' });
    expect([filters.minPrice, filters.maxPrice]).toEqual([3000, 6000]);
  });

  it('drops empty values, which would otherwise filter everything out', () => {
    const filters = parseFilters({ size: ['', 'M'], colour: '' });
    expect(filters.sizes).toEqual(['M']);
    expect(filters.colours).toEqual([]);
    expect(hasActiveFilters(parseFilters({ size: '' }))).toBe(false);
  });

  it('accepts a valid sort', () => {
    expect(parseFilters({ sort: 'price-desc' }).sort).toBe('price-desc');
  });
});

describe('parsePage', () => {
  it('reads whole numbers from 1 upwards', () => {
    expect(parsePage({ page: '3' })).toBe(3);
    expect(parsePage({})).toBe(1);
  });

  it.each(['0', '-2', '1.5', 'abc', ''])('falls back to 1 for %j', (value) => {
    expect(parsePage({ page: value })).toBe(1);
  });

  it('uses the first value when the param is repeated', () => {
    expect(parsePage({ page: ['2', '5'] })).toBe(2);
  });
});

describe('hasActiveFilters', () => {
  it('ignores sort but detects any real filter', () => {
    expect(hasActiveFilters({ ...noFilters, sort: 'price-asc' })).toBe(false);
    expect(hasActiveFilters({ ...noFilters, colours: ['Black'] })).toBe(true);
    expect(hasActiveFilters({ ...noFilters, minPrice: 0 })).toBe(true);
  });
});

describe('toQuery', () => {
  it('leaves out defaults so URLs stay short', () => {
    expect(buildQuery(toQuery(noFilters))).toBe('');
  });

  it('builds the same parameters the API expects', () => {
    const filters: CollectionFilters = {
      sizes: ['M', 'XL'],
      colours: ['Black'],
      minPrice: 3000,
      maxPrice: 9000,
      sort: 'price-desc',
    };

    expect(buildQuery(toQuery(filters, 2, 24))).toBe(
      '?size=M&size=XL&colour=Black&min=3000&max=9000&sort=price-desc&page=2&pageSize=24',
    );
  });

  it('round-trips through parseFilters', () => {
    const filters = parseFilters({
      size: ['S'],
      colour: ['Stone', 'Black'],
      min: '100',
      sort: 'newest',
    });
    const query = new URLSearchParams(buildQuery(toQuery(filters)));

    expect(
      parseFilters({
        size: query.getAll('size'),
        colour: query.getAll('colour'),
        min: query.get('min') ?? undefined,
        sort: query.get('sort') ?? undefined,
      }),
    ).toEqual(filters);
  });
});
