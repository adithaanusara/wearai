import type { Metadata } from 'next';
import Link from 'next/link';
import { notFound } from 'next/navigation';
import { ProductCard } from '@/components/product/ProductCard';
import { Container } from '@/components/ui/Container';
import { getCollection } from '@/data/collections';
import { products } from '@/data/products';
import {
  filterProducts,
  hasActiveFilters,
  parseFilters,
  sortProducts,
  type SearchParams,
} from '@/lib/collection';

interface CollectionPageProps {
  params: Promise<{ slug: string }>;
  searchParams: Promise<SearchParams>;
}

export async function generateMetadata({ params }: CollectionPageProps): Promise<Metadata> {
  const { slug } = await params;
  const collection = getCollection(slug);
  return { title: collection ? collection.title : 'Collection not found' };
}

export default async function CollectionPage({ params, searchParams }: CollectionPageProps) {
  const { slug } = await params;
  const collection = getCollection(slug);
  if (!collection) notFound();

  const filters = parseFilters(await searchParams);
  const inCollection = products.filter(collection.includes);
  const visible = sortProducts(filterProducts(inCollection, filters), filters.sort);

  return (
    <Container className="py-10 md:py-14">
      <h1 className="text-3xl font-bold tracking-wide uppercase md:text-4xl">{collection.title}</h1>
      <p className="text-muted mt-2 text-sm" role="status">
        {visible.length} {visible.length === 1 ? 'product' : 'products'}
      </p>

      {visible.length > 0 ? (
        <ul className="mt-8 grid grid-cols-2 gap-x-4 gap-y-10 lg:grid-cols-3">
          {visible.map((product) => (
            <li key={product.id}>
              <ProductCard product={product} imageSizes="(min-width: 1024px) 25vw, 50vw" />
            </li>
          ))}
        </ul>
      ) : (
        <div className="mt-16 text-center">
          <p className="text-lg font-medium">No products match your selection.</p>
          {hasActiveFilters(filters) && (
            <Link
              href={`/collections/${collection.slug}`}
              className="mt-4 inline-block text-sm underline"
            >
              Clear filters
            </Link>
          )}
        </div>
      )}
    </Container>
  );
}
