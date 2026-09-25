'use client';

import { useQueries, useQuery } from '@tanstack/react-query';
import { useCart } from '@/components/cart/CartProvider';
import { getProductsByIds, getRelatedProducts } from '@/lib/api';
import {
  buildCartLines,
  cartStatus,
  pickRecommendations,
  type CartLine,
  type ProductLookup,
} from '@/lib/cart';
import type { Product } from '@/types/product';

/**
 * The cart's items joined with product details from the API. Each product is fetched on its own,
 * so adding an item fetches only that one, and removing an item or changing a quantity fetches
 * nothing. The cart itself lives in the browser and is never touched by a failed request.
 */
export function useCartLines() {
  const { items } = useCart();
  const ids = [...new Set(items.map((item) => item.productId))];

  const results = useQueries({
    queries: ids.map((id) => ({
      queryKey: ['product-by-id', id],
      queryFn: async (): Promise<Product | null> => (await getProductsByIds([id])).items[0] ?? null,
    })),
  });

  const resultById = new Map(ids.map((id, index) => [id, results[index]]));
  const lines: CartLine[] = buildCartLines(items, (id): ProductLookup => {
    const result = resultById.get(id);
    if (!result || result.isPending) return { state: 'loading' };
    if (result.isError) return { state: 'error' };
    return result.data ? { state: 'found', product: result.data } : { state: 'missing' };
  });

  function retry() {
    results.forEach((result) => {
      if (result.isError) void result.refetch();
    });
  }

  return { lines, status: cartStatus(lines), retry };
}

/** Products to suggest next to the cart, based on the first item that has loaded. */
export function useCartRecommendations(lines: CartLine[], limit = 2): Product[] {
  const slug = lines.find((line) => line.product)?.product?.slug;

  const { data } = useQuery({
    queryKey: ['related-products', slug],
    queryFn: () => getRelatedProducts(slug as string, 8),
    enabled: Boolean(slug),
  });

  return pickRecommendations(data ?? [], lines, limit);
}
