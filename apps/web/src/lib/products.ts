import { products } from '@/data/products';
import type { Product } from '@/types/product';

export function getProductBySlug(slug: string): Product | undefined {
  return products.find((product) => product.slug === slug);
}

/** All colours of the same style, including the given product, in catalogue order. */
export function getColourways(product: Product): Product[] {
  return products.filter((item) => item.styleId === product.styleId);
}

/** Other products from the same category, excluding every colour of the given style. */
export function getRelatedProducts(product: Product, limit = 4): Product[] {
  return products
    .filter((item) => item.category === product.category && item.styleId !== product.styleId)
    .slice(0, limit);
}
