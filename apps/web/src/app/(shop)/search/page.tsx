import type { Metadata } from 'next';
import Link from 'next/link';
import { ProductCard } from '@/components/product/ProductCard';
import { Pagination } from '@/components/collection/Pagination';
import { ButtonLink } from '@/components/ui/ButtonLink';
import { Container } from '@/components/ui/Container';
import { MAX_QUERY_LENGTH, buildQuery, searchProducts } from '@/lib/api';
import { parsePage } from '@/lib/collection';

export const metadata: Metadata = { title: 'Search' };

interface SearchPageProps {
  searchParams: Promise<{ q?: string | string[]; page?: string | string[] }>;
}

const suggestions = [
  { label: 'New arrivals', href: '/collections/new' },
  { label: 'Women', href: '/collections/women' },
  { label: 'Men', href: '/collections/men' },
  { label: 'Accessories', href: '/collections/accessories' },
];

// Shows live store data, so it renders on each request and the build does not need the API.
export const dynamic = 'force-dynamic';

export default async function SearchPage({ searchParams }: SearchPageProps) {
  const params = await searchParams;
  const { q } = params;
  const query = (Array.isArray(q) ? q[0] : q)?.trim().slice(0, MAX_QUERY_LENGTH) ?? '';
  const page = parsePage(params);

  const found = query ? await searchProducts(query, page) : null;
  const results = found?.items ?? [];
  const total = found?.total ?? 0;
  const pageCount = found ? Math.max(1, Math.ceil(found.total / found.pageSize)) : 1;
  const hrefFor = (target: number) =>
    `/search${buildQuery({ q: query, page: target > 1 ? target : undefined })}`;

  return (
    <Container className="py-10 md:py-14">
      <h1 className="text-3xl font-bold tracking-wide uppercase md:text-4xl">Search</h1>

      <form action="/search" role="search" className="mt-6 flex max-w-xl gap-3">
        <label htmlFor="search-input" className="sr-only">
          Search products
        </label>
        <input
          id="search-input"
          name="q"
          type="search"
          defaultValue={query}
          placeholder="Search products"
          maxLength={MAX_QUERY_LENGTH}
          className="border-border bg-bg min-w-0 flex-1 rounded-sm border px-4 py-3 text-sm"
        />
        <button
          type="submit"
          className="bg-text text-bg hover:bg-dark-2 rounded-sm px-6 py-3 text-xs font-medium tracking-wide uppercase transition-colors"
        >
          Search
        </button>
      </form>

      {query && (
        <p className="text-muted mt-6 text-sm" role="status">
          {total} {total === 1 ? 'result' : 'results'} for “{query}”
        </p>
      )}

      {results.length > 0 ? (
        <ul className="mt-8 grid grid-cols-2 gap-x-4 gap-y-10 md:grid-cols-4">
          {results.map((product) => (
            <li key={product.id}>
              <ProductCard product={product} />
            </li>
          ))}
        </ul>
      ) : (
        <div className="mt-12 space-y-4 text-sm">
          <p>
            {query ? 'No products match your search.' : 'Type a product name, colour or category.'}
          </p>
          <ul className="flex flex-wrap gap-4">
            {suggestions.map((suggestion) => (
              <li key={suggestion.href}>
                <Link href={suggestion.href} className="underline">
                  {suggestion.label}
                </Link>
              </li>
            ))}
          </ul>
          {query && (
            <ButtonLink href="/contact" variant="secondary">
              Ask us about it
            </ButtonLink>
          )}
        </div>
      )}
      <Pagination page={page} pageCount={pageCount} hrefFor={hrefFor} />
    </Container>
  );
}
