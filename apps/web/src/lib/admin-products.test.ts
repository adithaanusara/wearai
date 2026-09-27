import { describe, expect, it } from 'vitest';
import {
  formValuesFor,
  toProductEdit,
  validateProductForm,
  type ProductFormValues,
} from '@/lib/admin-products';

const valid: ProductFormValues = {
  name: 'Essential Fitted Tee',
  price: '3250',
  compareAtPrice: '',
  description: 'A soft tee.',
};

describe('validateProductForm', () => {
  it('accepts a valid form, with or without a compare-at price', () => {
    expect(validateProductForm(valid)).toEqual({});
    expect(validateProductForm({ ...valid, compareAtPrice: '4000' })).toEqual({});
  });

  it('needs a name and a description', () => {
    const errors = validateProductForm({ ...valid, name: '  ', description: '' });
    expect(errors.name).toBeDefined();
    expect(errors.description).toBeDefined();
  });

  it('limits the lengths', () => {
    expect(validateProductForm({ ...valid, name: 'x'.repeat(121) }).name).toBeDefined();
    expect(
      validateProductForm({ ...valid, description: 'x'.repeat(2001) }).description,
    ).toBeDefined();
    expect(validateProductForm({ ...valid, name: 'x'.repeat(120) }).name).toBeUndefined();
  });

  it.each(['', '-1', '12.5', '1e3', 'abc', '١٢٣', '100000001'])('rejects the price %j', (price) => {
    expect(validateProductForm({ ...valid, price }).price).toBeDefined();
  });

  it('accepts a price of 0 and the maximum', () => {
    expect(validateProductForm({ ...valid, price: '0' }).price).toBeUndefined();
    expect(validateProductForm({ ...valid, price: '100000000' }).price).toBeUndefined();
  });

  it('needs a compare-at price above the price', () => {
    expect(validateProductForm({ ...valid, compareAtPrice: '3250' }).compareAtPrice).toBeDefined();
    expect(validateProductForm({ ...valid, compareAtPrice: '3000' }).compareAtPrice).toBeDefined();
    expect(
      validateProductForm({ ...valid, compareAtPrice: '3251' }).compareAtPrice,
    ).toBeUndefined();
  });

  it('rejects a malformed compare-at price', () => {
    expect(validateProductForm({ ...valid, compareAtPrice: '4.5' }).compareAtPrice).toBeDefined();
  });
});

describe('toProductEdit', () => {
  it('trims text and turns prices into numbers', () => {
    expect(
      toProductEdit({ name: ' Tee ', price: ' 3500 ', compareAtPrice: '4000', description: ' d ' }),
    ).toEqual({ name: 'Tee', price: 3500, compareAtPrice: 4000, description: 'd' });
  });

  it('sends null for an empty compare-at price', () => {
    expect(toProductEdit(valid).compareAtPrice).toBeNull();
  });
});

describe('formValuesFor', () => {
  it('shows a missing compare-at price as empty', () => {
    expect(formValuesFor({ name: 'a', price: 5, compareAtPrice: null, description: 'd' })).toEqual({
      name: 'a',
      price: '5',
      compareAtPrice: '',
      description: 'd',
    });
  });
});
