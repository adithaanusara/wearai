import Link from 'next/link';
import { ProductCard } from '@/components/product/ProductCard';
import { Container } from '@/components/ui/Container';
import { products } from '@/data/products';

export function AccessoriesGrid() {
  const accessories = products.filter((product) => product.gender === 'unisex');

  return (
    <section aria-labelledby="accessories-title" className="bg-surface py-12 md:py-16">
      <Container>
        <div className="mb-6 flex items-end justify-between gap-4">
          <h2
            id="accessories-title"
            className="text-2xl font-bold tracking-wide uppercase md:text-3xl"
          >
            Accessories
          </h2>
          <Link
            href="/collections/accessories"
            className="text-xs font-medium tracking-wide uppercase underline"
          >
            Shop all
          </Link>
        </div>
        <ul className="grid grid-cols-2 gap-4 md:grid-cols-4">
          {accessories.map((product) => (
            <li key={product.id}>
              <ProductCard product={product} />
            </li>
          ))}
        </ul>
      </Container>
    </section>
  );
}
