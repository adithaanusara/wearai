import { describe, expect, it } from 'vitest';
import {
  MAX_QUANTITY,
  buildCartLines,
  canCheckout,
  cartCount,
  cartReducer,
  cartStatus,
  cartSubtotal,
  hasCartProblems,
  parseStoredCart,
  pickRecommendations,
  type ProductLookup,
} from '@/lib/cart';
import type { CartItem } from '@/types/cart';
import type { Product } from '@/types/product';

const line = (productId: string, size: string, quantity = 1): CartItem => ({
  productId,
  size,
  quantity,
});

describe('cartReducer', () => {
  it('adds a new line with quantity 1', () => {
    expect(cartReducer([], { type: 'add', productId: 'w-tee-01', size: 'M' })).toEqual([
      line('w-tee-01', 'M'),
    ]);
  });

  it('increases the quantity when the same product and size is added again', () => {
    const items = [line('w-tee-01', 'M')];
    expect(cartReducer(items, { type: 'add', productId: 'w-tee-01', size: 'M' })).toEqual([
      line('w-tee-01', 'M', 2),
    ]);
  });

  it('keeps different sizes of a product as separate lines', () => {
    const items = [line('w-tee-01', 'M')];
    expect(cartReducer(items, { type: 'add', productId: 'w-tee-01', size: 'L' })).toHaveLength(2);
  });

  it('caps the quantity', () => {
    const items = [line('w-tee-01', 'M', MAX_QUANTITY)];
    const next = cartReducer(items, { type: 'add', productId: 'w-tee-01', size: 'M' });
    expect(next[0].quantity).toBe(MAX_QUANTITY);
  });

  it('sets the quantity, clamped to the limit', () => {
    const items = [line('w-tee-01', 'M')];
    const next = cartReducer(items, {
      type: 'setQuantity',
      productId: 'w-tee-01',
      size: 'M',
      quantity: 99,
    });
    expect(next[0].quantity).toBe(MAX_QUANTITY);
  });

  it('removes a line when the quantity is set to zero', () => {
    const items = [line('w-tee-01', 'M', 2)];
    expect(
      cartReducer(items, { type: 'setQuantity', productId: 'w-tee-01', size: 'M', quantity: 0 }),
    ).toEqual([]);
  });

  it('removes only the matching line', () => {
    const items = [line('w-tee-01', 'M'), line('w-tee-01', 'L')];
    expect(cartReducer(items, { type: 'remove', productId: 'w-tee-01', size: 'M' })).toEqual([
      line('w-tee-01', 'L'),
    ]);
  });

  it('clears and loads', () => {
    const items = [line('w-tee-01', 'M')];
    expect(cartReducer(items, { type: 'clear' })).toEqual([]);
    expect(cartReducer([], { type: 'load', items })).toEqual(items);
  });

  it('does not change the previous state', () => {
    const items = [line('w-tee-01', 'M')];
    cartReducer(items, { type: 'add', productId: 'w-tee-01', size: 'M' });
    expect(items).toEqual([line('w-tee-01', 'M')]);
  });
});

function product(overrides: Partial<Product> & Pick<Product, 'id'>): Product {
  return {
    slug: overrides.id,
    styleId: overrides.id,
    name: overrides.id,
    gender: 'women',
    category: 't-shirts',
    colour: 'Black',
    price: 1000,
    images: ['/a.svg'],
    sizes: ['S', 'M'],
    isNew: false,
    description: '',
    details: [],
    ...overrides,
  };
}

describe('cart totals', () => {
  it('counts every unit in the cart', () => {
    expect(cartCount([line('a', 'M', 2), line('b', 'L', 3)])).toBe(5);
  });
});

/** A lookup where the given products are found and everything else is missing. */
const knownProducts =
  (catalogue: Product[]) =>
  (id: string): ProductLookup => {
    const found = catalogue.find((candidate) => candidate.id === id);
    return found ? { state: 'found', product: found } : { state: 'missing' };
  };

describe('buildCartLines', () => {
  const catalogue = [
    product({ id: 'tee', price: 3250, sizes: ['S', 'M'] }),
    product({ id: 'jog', price: 7450, sizes: ['M', 'L'] }),
  ];
  const lookup = knownProducts(catalogue);

  it('prices each line from the loaded products', () => {
    const lines = buildCartLines([line('tee', 'M', 2), line('jog', 'L')], lookup);

    expect(lines.map((entry) => entry.total)).toEqual([6500, 7450]);
    expect(lines.map((entry) => entry.problem)).toEqual([null, null]);
    expect(cartSubtotal(lines)).toBe(13950);
    expect(hasCartProblems(lines)).toBe(false);
    expect(canCheckout(lines)).toBe(true);
  });

  it('keeps the order of the cart, not of the products', () => {
    const lines = buildCartLines([line('jog', 'M'), line('tee', 'S')], lookup);

    expect(lines.map((entry) => entry.item.productId)).toEqual(['jog', 'tee']);
  });

  it('flags a product that no longer exists instead of dropping it', () => {
    const lines = buildCartLines([line('tee', 'M'), line('gone', 'M')], lookup);

    expect(lines[1]).toMatchObject({
      state: 'ready',
      problem: 'unavailable',
      product: null,
      total: 0,
    });
    expect(hasCartProblems(lines)).toBe(true);
    expect(canCheckout(lines)).toBe(false);
  });

  it('flags a size the product no longer has', () => {
    const lines = buildCartLines([line('tee', 'XL')], lookup);

    expect(lines[0]).toMatchObject({ problem: 'size', total: 0 });
    expect(lines[0].product?.id).toBe('tee');
  });

  it('leaves flagged lines out of the subtotal', () => {
    const lines = buildCartLines([line('tee', 'M'), line('gone', 'M'), line('jog', 'S')], lookup);

    expect(cartSubtotal(lines)).toBe(3250);
  });

  it('marks lines that are still loading or failed, without calling them unavailable', () => {
    const lines = buildCartLines([line('a', 'M'), line('b', 'M')], (id) =>
      id === 'a' ? { state: 'loading' } : { state: 'error' },
    );

    expect(lines.map((entry) => entry.state)).toEqual(['loading', 'error']);
    expect(lines.map((entry) => entry.problem)).toEqual([null, null]);
    expect(canCheckout(lines)).toBe(false);
  });

  it('handles an empty cart', () => {
    expect(buildCartLines([], lookup)).toEqual([]);
  });
});

describe('cartStatus', () => {
  const state = (value: ProductLookup['state']) =>
    buildCartLines([line('a', 'M')], () =>
      value === 'found'
        ? { state: 'found', product: product({ id: 'a' }) }
        : ({ state: value } as ProductLookup),
    );

  it('describes the cart as a whole', () => {
    expect(cartStatus([])).toBe('empty');
    expect(cartStatus(state('loading'))).toBe('loading');
    expect(cartStatus(state('error'))).toBe('error');
    expect(cartStatus(state('found'))).toBe('ready');
    expect(cartStatus(state('missing'))).toBe('ready');
  });

  it('reports an error even while other lines are still loading', () => {
    const lines = buildCartLines([line('a', 'M'), line('b', 'M')], (id) =>
      id === 'a' ? { state: 'loading' } : { state: 'error' },
    );

    expect(cartStatus(lines)).toBe('error');
  });

  it('cannot check out an empty cart', () => {
    expect(canCheckout([])).toBe(false);
  });
});

describe('pickRecommendations', () => {
  const tee = product({ id: 'tee', styleId: 'tee-style' });
  const hoodie = product({ id: 'hoodie', styleId: 'hoodie-style' });
  const hoodieBlack = product({ id: 'hoodie-black', styleId: 'hoodie-style' });
  const cap = product({ id: 'cap', styleId: 'cap-style' });
  const inCart = buildCartLines([line('tee', 'M')], knownProducts([tee]));

  it('skips styles already in the cart', () => {
    const suggestions = pickRecommendations([tee, hoodie, cap], inCart);

    expect(suggestions.map((p) => p.id)).toEqual(['hoodie', 'cap']);
  });

  it('suggests each style once, even when it comes in several colours', () => {
    const suggestions = pickRecommendations([hoodie, hoodieBlack, cap], inCart, 5);

    expect(suggestions.map((p) => p.id)).toEqual(['hoodie', 'cap']);
  });

  it('respects the limit', () => {
    expect(pickRecommendations([hoodie, cap], inCart, 1)).toHaveLength(1);
  });

  it('copes with unavailable lines in the cart', () => {
    const lines = buildCartLines([line('gone', 'M')], knownProducts([]));

    expect(pickRecommendations([tee, hoodie], lines).map((p) => p.id)).toEqual(['tee', 'hoodie']);
  });

  it('returns nothing when there is nothing to suggest', () => {
    expect(pickRecommendations([], inCart)).toEqual([]);
  });
});

describe('parseStoredCart', () => {
  it('returns an empty cart for missing or invalid JSON', () => {
    expect(parseStoredCart(null)).toEqual([]);
    expect(parseStoredCart('not json')).toEqual([]);
    expect(parseStoredCart('{"a":1}')).toEqual([]);
  });

  it('keeps valid lines and drops malformed ones', () => {
    const raw = JSON.stringify([
      { productId: 'w-tee-01', size: 'M', quantity: 2 },
      { productId: 5, size: 'M', quantity: 1 },
      { productId: 'w-tee-01', size: 'L', quantity: 'many' },
      { productId: 'w-tee-01', size: 'S', quantity: 0 },
      null,
    ]);
    expect(parseStoredCart(raw)).toEqual([line('w-tee-01', 'M', 2)]);
  });

  it('clamps stored quantities', () => {
    const raw = JSON.stringify([{ productId: 'w-tee-01', size: 'M', quantity: 500 }]);
    expect(parseStoredCart(raw)[0].quantity).toBe(MAX_QUANTITY);
  });
});
