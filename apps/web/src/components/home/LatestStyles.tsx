import Link from 'next/link';
import { ProductCard } from '@/components/product/ProductCard';
import { Carousel } from '@/components/ui/Carousel';
import { Container } from '@/components/ui/Container';
import type { Product } from '@/types/product';

const slideImageSizes = '(min-width: 1024px) 24vw, (min-width: 640px) 40vw, 70vw';

export function LatestStyles({ products }: { products: Product[] }) {
  return (
    <section aria-labelledby="latest-styles-title" className="py-12 md:py-16">
      <Container>
        <div className="mb-6 flex items-end justify-between gap-4">
          <h2
            id="latest-styles-title"
            className="text-2xl font-bold tracking-wide uppercase md:text-3xl"
          >
            Shop the latest styles
          </h2>
          <Link
            href="/collections/new"
            className="text-xs font-medium tracking-wide uppercase underline"
          >
            Shop all
          </Link>
        </div>

        <Carousel label="Latest styles">
          {products.map((product) => (
            <li key={product.id} className="w-[70%] shrink-0 snap-start sm:w-[40%] lg:w-[24%]">
              <ProductCard product={product} imageSizes={slideImageSizes} />
            </li>
          ))}
        </Carousel>
      </Container>
    </section>
  );
}
