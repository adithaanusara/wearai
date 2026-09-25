import type { Metadata } from 'next';
import Link from 'next/link';
import { ProductCard } from '@/components/product/ProductCard';
import { ButtonLink } from '@/components/ui/ButtonLink';
import { Container } from '@/components/ui/Container';
import { products } from '@/data/products';
import { MAX_QUERY_LENGTH, searchProducts } from '@/lib/search';

export const metadata: Metadata = { title: 'Search' };

interface SearchPageProps {
  searchParams: Promise<{ q?: string | string[] }>;
}

const suggestions = [
  { label: 'New arrivals', href: '/collections/new' },
  { label: 'Women', href: '/collections/women' },
  { label: 'Men', href: '/collections/men' },
  { label: 'Accessories', href: '/collections/accessories' },
];

export default async function SearchPage({ searchParams }: SearchPageProps) {
  const { q } = await searchParams;
  const query = (Array.isArray(q) ? q[0] : q)?.trim().slice(0, MAX_QUERY_LENGTH) ?? '';
  const results = searchProducts(query, products);

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
          {results.length} {results.length === 1 ? 'result' : 'results'} for “{query}”
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
    </Container>
  );
}
