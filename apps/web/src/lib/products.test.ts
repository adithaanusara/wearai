import { describe, expect, it } from 'vitest';
import { products } from '@/data/products';
import { getColourways, getProductBySlug, getRelatedProducts } from '@/lib/products';

describe('catalogue data', () => {
  it('has unique ids and slugs', () => {
    expect(new Set(products.map((p) => p.id)).size).toBe(products.length);
    expect(new Set(products.map((p) => p.slug)).size).toBe(products.length);
  });
});

describe('getProductBySlug', () => {
  it('finds a product and returns undefined for unknown slugs', () => {
    expect(getProductBySlug('tapered-joggers')?.id).toBe('m-jog-01');
    expect(getProductBySlug('nope')).toBeUndefined();
  });
});

describe('getColourways', () => {
  it('returns every colour of a style, including the product itself', () => {
    const hoodie = getProductBySlug('pullover-hoodie')!;
    expect(getColourways(hoodie).map((p) => p.colour)).toEqual(['Dark Grey', 'Black']);
  });

  it('returns just the product when it has no other colours', () => {
    const joggers = getProductBySlug('tapered-joggers')!;
    expect(getColourways(joggers)).toEqual([joggers]);
  });
});

describe('getRelatedProducts', () => {
  it('stays in the category, skips the same style and respects the limit', () => {
    const leggings = getProductBySlug('seamless-high-rise-leggings')!;
    const related = getRelatedProducts(leggings, 1);
    expect(related).toHaveLength(1);
    expect(related[0].category).toBe('leggings');
    expect(related[0].styleId).not.toBe(leggings.styleId);
  });
});
