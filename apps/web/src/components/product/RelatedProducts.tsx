import { ProductCard } from '@/components/product/ProductCard';
import type { Product } from '@/types/product';

export function RelatedProducts({ products }: { products: Product[] }) {
  if (products.length === 0) return null;

  return (
    <section aria-labelledby="related-title">
      <h2 id="related-title" className="text-xl font-bold tracking-wide uppercase">
        You may also like
      </h2>
      <ul className="mt-6 grid grid-cols-2 gap-4 lg:grid-cols-4">
        {products.map((product) => (
          <li key={product.id}>
            <ProductCard product={product} />
          </li>
        ))}
      </ul>
    </section>
  );
}
