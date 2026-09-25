import { describe, expect, it } from 'vitest';
import { products } from '@/data/products';
import { searchProducts } from '@/lib/search';

const names = (query: string) => searchProducts(query, products).map((product) => product.name);

describe('searchProducts', () => {
  it('returns nothing for an empty or blank query', () => {
    expect(searchProducts('', products)).toEqual([]);
    expect(searchProducts('   ', products)).toEqual([]);
  });

  it('matches names case-insensitively', () => {
    expect(names('HOODIE')).toContain('Pullover Hoodie');
  });

  it('requires every word to match', () => {
    const results = searchProducts('black hoodie', products);
    expect(results.length).toBeGreaterThan(0);
    expect(results.every((product) => product.colour === 'Black')).toBe(true);
    expect(results.every((product) => product.category === 'hoodies')).toBe(true);
  });

  it('matches category and colour words that are not in the name', () => {
    expect(searchProducts('leggings', products).length).toBeGreaterThanOrEqual(3);
    expect(searchProducts('stone', products).map((product) => product.colour)).toEqual(['Stone']);
  });

  it('does not let "men" match women\'s products', () => {
    const results = searchProducts('men', products);
    expect(results.length).toBeGreaterThan(0);
    expect(results.every((product) => product.gender === 'men')).toBe(true);
  });

  it('ranks name matches above other matches', () => {
    // "black" is a colour for many products but is never in a name, so a name match must come first.
    const results = searchProducts('cap black', products);
    expect(results[0].name).toBe('Everyday Cap');
  });

  it('returns nothing for a word that matches no product', () => {
    expect(searchProducts('zzzz', products)).toEqual([]);
  });

  it('ignores punctuation and does not choke on regex characters', () => {
    expect(names('hoodie!!')).toContain('Pullover Hoodie');
    expect(searchProducts('(*[', products)).toEqual([]);
  });
});
