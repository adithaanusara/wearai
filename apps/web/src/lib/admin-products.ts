import type { ProductEdit } from '@/lib/api';

/** The form's values, as typed. Prices stay text until they are checked. */
export interface ProductFormValues {
  name: string;
  price: string;
  compareAtPrice: string;
  description: string;
}

export const PRODUCT_FIELDS = ['name', 'price', 'compareAtPrice', 'description'] as const;
export type ProductField = (typeof PRODUCT_FIELDS)[number];

const MAX_PRICE = 100_000_000;
const WHOLE_NUMBER = /^[0-9]+$/;

/** One message per invalid field. The API checks everything again; this just saves a round trip. */
export function validateProductForm(
  values: ProductFormValues,
): Partial<Record<ProductField, string>> {
  const errors: Partial<Record<ProductField, string>> = {};
  const name = values.name.trim();
  const price = values.price.trim();
  const compareAt = values.compareAtPrice.trim();
  const description = values.description.trim();

  if (!name || name.length > 120) errors.name = 'Enter a name of up to 120 characters.';

  if (!WHOLE_NUMBER.test(price) || Number(price) > MAX_PRICE) {
    errors.price = 'Enter the price in whole rupees, such as 4450.';
  }
  if (compareAt) {
    if (!WHOLE_NUMBER.test(compareAt) || Number(compareAt) > MAX_PRICE) {
      errors.compareAtPrice = 'Enter the compare-at price in whole rupees, or leave it empty.';
    } else if (!errors.price && Number(compareAt) <= Number(price)) {
      errors.compareAtPrice = 'The compare-at price must be higher than the price.';
    }
  }

  if (!description || description.length > 2000) {
    errors.description = 'Enter a description of up to 2,000 characters.';
  }
  return errors;
}

/** The request body for values that passed `validateProductForm`. */
export function toProductEdit(values: ProductFormValues): ProductEdit {
  const compareAt = values.compareAtPrice.trim();
  return {
    name: values.name.trim(),
    price: Number(values.price.trim()),
    compareAtPrice: compareAt ? Number(compareAt) : null,
    description: values.description.trim(),
  };
}

export function formValuesFor(product: {
  name: string;
  price: number;
  compareAtPrice: number | null;
  description: string;
}): ProductFormValues {
  return {
    name: product.name,
    price: String(product.price),
    compareAtPrice: product.compareAtPrice === null ? '' : String(product.compareAtPrice),
    description: product.description,
  };
}
