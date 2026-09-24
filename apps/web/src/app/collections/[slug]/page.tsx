import type { Metadata } from 'next';
import Link from 'next/link';
import { notFound } from 'next/navigation';
import { FilterDrawer } from '@/components/collection/FilterDrawer';
import { FilterPanel } from '@/components/collection/FilterPanel';
import { SortSelect } from '@/components/collection/SortSelect';
import { ProductCard } from '@/components/product/ProductCard';
import { Container } from '@/components/ui/Container';
import { getCollection } from '@/data/collections';
import { products } from '@/data/products';
import {
  filterProducts,
  getFilterOptions,
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
  const options = getFilterOptions(inCollection);
  const visible = sortProducts(filterProducts(inCollection, filters), filters.sort);

  return (
    <Container className="py-10 md:py-14">
      <div className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold tracking-wide uppercase md:text-4xl">
            {collection.title}
          </h1>
          <p className="text-muted mt-2 text-sm" role="status">
            {visible.length} {visible.length === 1 ? 'product' : 'products'}
          </p>
        </div>
        <div className="flex items-center gap-3">
          <FilterDrawer options={options} filters={filters} resultCount={visible.length} />
          <SortSelect value={filters.sort} />
        </div>
      </div>

      <div className="mt-8 gap-10 lg:grid lg:grid-cols-[14rem_1fr]">
        <aside aria-label="Filters" className="hidden lg:block">
          <FilterPanel options={options} filters={filters} />
        </aside>
        <div>
          {visible.length > 0 ? (
            <ul className="grid grid-cols-2 gap-x-4 gap-y-10 lg:grid-cols-3">
              {visible.map((product) => (
                <li key={product.id}>
                  <ProductCard product={product} imageSizes="(min-width: 1024px) 25vw, 50vw" />
                </li>
              ))}
            </ul>
          ) : (
            <div className="py-16 text-center">
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
        </div>
      </div>
    </Container>
  );
}
