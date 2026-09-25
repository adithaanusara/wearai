import type { Product } from '@/types/product';

export const MAX_QUERY_LENGTH = 100;

const words = (text: string) =>
  text
    .toLowerCase()
    .split(/[^a-z0-9]+/)
    .filter(Boolean);

/**
 * Finds products where every search word starts a word in the name, colour, category or gender.
 * Name matches rank highest. Matching starts at word boundaries, so "men" does not find women's items.
 */
export function searchProducts(query: string, catalogue: Product[]): Product[] {
  const terms = words(query.slice(0, MAX_QUERY_LENGTH));
  if (terms.length === 0) return [];

  const scored = catalogue.flatMap((product, index) => {
    const nameWords = words(product.name);
    const otherWords = words(`${product.colour} ${product.category} ${product.gender}`);
    let score = 0;

    for (const term of terms) {
      if (nameWords.some((word) => word.startsWith(term))) score += 3;
      else if (otherWords.some((word) => word.startsWith(term))) score += 1;
      else return [];
    }
    return [{ product, score, index }];
  });

  // Higher score first; ties keep the catalogue order.
  return scored
    .sort((a, b) => b.score - a.score || a.index - b.index)
    .map((entry) => entry.product);
}
