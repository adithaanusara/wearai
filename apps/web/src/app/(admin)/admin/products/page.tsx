import type { Metadata } from 'next';
import Link from 'next/link';
import { Pagination } from '@/components/collection/Pagination';
import { buildQuery, getAdminProducts } from '@/lib/api';
import { parsePage, type SearchParams } from '@/lib/collection';
import { formatPrice } from '@/lib/format';
import { requireRole, serverAuthHeaders } from '@/lib/server-session';

export const metadata: Metadata = { title: 'Products' };

const FILTERS = [
  { value: 'all', label: 'All' },
  { value: 'active', label: 'In the shop' },
  { value: 'archived', label: 'Archived' },
];

const first = (value: string | string[] | undefined) => (Array.isArray(value) ? value[0] : value);

export default async function AdminProductsPage({
  searchParams,
}: {
  searchParams: Promise<SearchParams>;
}) {
  await requireRole('staff');
  const params = await searchParams;
  const page = parsePage(params);
  const search = first(params.q)?.trim().slice(0, 100) || undefined;
  const archived =
    FILTERS.find((option) => option.value === first(params.archived))?.value ?? 'all';

  const products = await getAdminProducts({ search, archived, page }, await serverAuthHeaders());
  const pageCount = Math.max(1, Math.ceil(products.total / products.pageSize));

  return (
    <div className="space-y-8">
      <h1 className="text-3xl font-bold tracking-wide uppercase">Products</h1>

      <form method="get" role="search" className="flex flex-wrap items-end gap-3">
        <div>
          <label htmlFor="product-search" className="text-muted mb-1 block text-xs">
            Name, id, category or colour
          </label>
          <input
            id="product-search"
            name="q"
            type="search"
            defaultValue={search}
            maxLength={100}
            className="border-border bg-bg w-64 max-w-full rounded-sm border px-3 py-2 text-sm"
          />
        </div>
        <div>
          <label htmlFor="product-archived" className="text-muted mb-1 block text-xs">
            Show
          </label>
          <select
            id="product-archived"
            name="archived"
            defaultValue={archived}
            className="border-border bg-bg rounded-sm border px-3 py-2 text-sm"
          >
            {FILTERS.map((option) => (
              <option key={option.value} value={option.value}>
                {option.label}
              </option>
            ))}
          </select>
        </div>
        <button
          type="submit"
          className="bg-text text-bg rounded-sm px-5 py-2 text-xs font-medium tracking-wide uppercase"
        >
          Filter
        </button>
      </form>

      <p className="text-muted text-sm">
        {products.total} {products.total === 1 ? 'product' : 'products'}
      </p>

      {products.items.length === 0 ? (
        <p className="text-sm">No products match.</p>
      ) : (
        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm">
            <caption className="sr-only">Products</caption>
            <thead className="text-muted text-xs">
              <tr className="border-border border-b">
                <th scope="col" className="py-2 pr-4 font-normal">
                  Product
                </th>
                <th scope="col" className="py-2 pr-4 font-normal">
                  Category
                </th>
                <th scope="col" className="py-2 pr-4 font-normal">
                  Status
                </th>
                <th scope="col" className="py-2 text-right font-normal">
                  Price
                </th>
              </tr>
            </thead>
            <tbody className="divide-border divide-y">
              {products.items.map((product) => (
                <tr key={product.id}>
                  <td className="py-3 pr-4">
                    <Link
                      href={`/admin/products/${encodeURIComponent(product.id)}`}
                      className="font-medium underline"
                    >
                      {product.name}
                    </Link>
                    <span className="text-muted block text-xs">
                      {product.id} &middot; {product.colour}
                    </span>
                  </td>
                  <td className="py-3 pr-4 whitespace-nowrap">
                    {product.category} ({product.gender})
                  </td>
                  <td className="py-3 pr-4">
                    <span className="border-border rounded-sm border px-2 py-1 text-xs">
                      {product.archived ? 'Archived' : 'In the shop'}
                    </span>
                  </td>
                  <td className="py-3 text-right whitespace-nowrap">
                    {formatPrice(product.price)}
                    {product.compareAtPrice !== null && (
                      <span className="text-muted block text-xs line-through">
                        {formatPrice(product.compareAtPrice)}
                      </span>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      <Pagination
        page={page}
        pageCount={pageCount}
        hrefFor={(target) =>
          `/admin/products${buildQuery({
            q: search,
            archived: archived === 'all' ? undefined : archived,
            page: target > 1 ? target : undefined,
          })}`
        }
      />
    </div>
  );
}
