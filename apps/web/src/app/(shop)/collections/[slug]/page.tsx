import type { Metadata } from 'next';
import Link from 'next/link';
import { FilterDrawer } from '@/components/collection/FilterDrawer';
import { FilterPanel } from '@/components/collection/FilterPanel';
import { Pagination } from '@/components/collection/Pagination';
import { SortSelect } from '@/components/collection/SortSelect';
import { ProductCard } from '@/components/product/ProductCard';
import { Container } from '@/components/ui/Container';
import { ApiError, buildQuery, getCollection, orNotFound } from '@/lib/api';
import {
  hasActiveFilters,
  parseFilters,
  parsePage,
  toQuery,
  type SearchParams,
} from '@/lib/collection';

interface CollectionPageProps {
  params: Promise<{ slug: string }>;
  searchParams: Promise<SearchParams>;
}

export async function generateMetadata({ params }: CollectionPageProps): Promise<Metadata> {
  const { slug } = await params;
  try {
    const collection = await getCollection(slug, { pageSize: 1 });
    return { title: collection.title };
  } catch (error) {
    if (error instanceof ApiError && error.status === 404) {
      return { title: 'Collection not found' };
    }
    throw error;
  }
}

// Shows live store data, so it renders on each request and the build does not need the API.
export const dynamic = 'force-dynamic';

export default async function CollectionPage({ params, searchParams }: CollectionPageProps) {
  const { slug } = await params;
  const query = await searchParams;
  const filters = parseFilters(query);
  const page = parsePage(query);

  const collection = await orNotFound(getCollection(slug, toQuery(filters, page)));
  const { items, total, pageSize, filterOptions } = collection;
  const pageCount = Math.max(1, Math.ceil(total / pageSize));
  const hrefFor = (target: number) =>
    `/collections/${collection.slug}${buildQuery(toQuery(filters, target))}`;

  return (
    <Container className="py-10 md:py-14">
      <div className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold tracking-wide uppercase md:text-4xl">
            {collection.title}
          </h1>
          <p className="text-muted mt-2 text-sm" role="status">
            {total} {total === 1 ? 'product' : 'products'}
          </p>
        </div>
        <div className="flex items-center gap-3">
          <FilterDrawer options={filterOptions} filters={filters} resultCount={total} />
          <SortSelect value={filters.sort} />
        </div>
      </div>

      <div className="mt-8 gap-10 lg:grid lg:grid-cols-[14rem_1fr]">
        <aside aria-label="Filters" className="hidden lg:block">
          <FilterPanel options={filterOptions} filters={filters} />
        </aside>
        <div>
          {items.length > 0 ? (
            <ul className="grid grid-cols-2 gap-x-4 gap-y-10 lg:grid-cols-3">
              {items.map((product) => (
                <li key={product.id}>
                  <ProductCard product={product} imageSizes="(min-width: 1024px) 25vw, 50vw" />
                </li>
              ))}
            </ul>
          ) : (
            <div className="py-16 text-center">
              <p className="text-lg font-medium">No products match your selection.</p>
              {(hasActiveFilters(filters) || page > 1) && (
                <Link
                  href={`/collections/${collection.slug}`}
                  className="mt-4 inline-block text-sm underline"
                >
                  {hasActiveFilters(filters) ? 'Clear filters' : 'Back to the first page'}
                </Link>
              )}
            </div>
          )}
          <Pagination page={page} pageCount={pageCount} hrefFor={hrefFor} />
        </div>
      </div>
    </Container>
  );
}
