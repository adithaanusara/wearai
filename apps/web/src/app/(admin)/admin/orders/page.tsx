import type { Metadata } from 'next';
import Link from 'next/link';
import { Pagination } from '@/components/collection/Pagination';
import { orderStatuses } from '@/lib/admin';
import { buildQuery, getAdminOrders } from '@/lib/api';
import { parsePage, type SearchParams } from '@/lib/collection';
import { formatDate, formatPrice } from '@/lib/format';
import { statusLabel } from '@/lib/orders';
import { requireRole, serverAuthHeaders } from '@/lib/server-session';

export const metadata: Metadata = { title: 'Orders' };

const first = (value: string | string[] | undefined) => (Array.isArray(value) ? value[0] : value);

export default async function AdminOrdersPage({
  searchParams,
}: {
  searchParams: Promise<SearchParams>;
}) {
  await requireRole('staff');
  const params = await searchParams;
  const page = parsePage(params);
  const search = first(params.q)?.trim().slice(0, 100) || undefined;
  const status = orderStatuses.find((option) => option === first(params.status));

  const orders = await getAdminOrders({ search, status, page }, await serverAuthHeaders());
  const pageCount = Math.max(1, Math.ceil(orders.total / orders.pageSize));

  return (
    <div className="space-y-8">
      <h1 className="text-3xl font-bold tracking-wide uppercase">Orders</h1>

      <form method="get" role="search" className="flex flex-wrap items-end gap-3">
        <div>
          <label htmlFor="order-search" className="text-muted mb-1 block text-xs">
            Reference, email or name
          </label>
          <input
            id="order-search"
            name="q"
            type="search"
            defaultValue={search}
            maxLength={100}
            className="border-border bg-bg w-64 max-w-full rounded-sm border px-3 py-2 text-sm"
          />
        </div>
        <div>
          <label htmlFor="order-status" className="text-muted mb-1 block text-xs">
            Status
          </label>
          <select
            id="order-status"
            name="status"
            defaultValue={status ?? ''}
            className="border-border bg-bg rounded-sm border px-3 py-2 text-sm"
          >
            <option value="">All</option>
            {orderStatuses.map((option) => (
              <option key={option} value={option}>
                {statusLabel(option)}
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
        {orders.total} {orders.total === 1 ? 'order' : 'orders'}
      </p>

      {orders.items.length === 0 ? (
        <p className="text-sm">No orders match.</p>
      ) : (
        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm">
            <caption className="sr-only">Orders, newest first</caption>
            <thead className="text-muted text-xs">
              <tr className="border-border border-b">
                <th scope="col" className="py-2 pr-4 font-normal">
                  Order
                </th>
                <th scope="col" className="py-2 pr-4 font-normal">
                  Date
                </th>
                <th scope="col" className="py-2 pr-4 font-normal">
                  Customer
                </th>
                <th scope="col" className="py-2 pr-4 font-normal">
                  Status
                </th>
                <th scope="col" className="py-2 text-right font-normal">
                  Total
                </th>
              </tr>
            </thead>
            <tbody className="divide-border divide-y">
              {orders.items.map((order) => (
                <tr key={order.reference}>
                  <td className="py-3 pr-4 font-medium whitespace-nowrap">
                    <Link
                      href={`/admin/orders/${encodeURIComponent(order.reference)}`}
                      className="underline"
                    >
                      {order.reference}
                    </Link>
                  </td>
                  <td className="py-3 pr-4 whitespace-nowrap">{formatDate(order.createdAt)}</td>
                  <td className="py-3 pr-4 break-all">
                    {order.fullName}
                    <span className="text-muted block text-xs">{order.email}</span>
                  </td>
                  <td className="py-3 pr-4">
                    <span className="border-border rounded-sm border px-2 py-1 text-xs">
                      {statusLabel(order.status)}
                    </span>
                  </td>
                  <td className="py-3 text-right whitespace-nowrap">{formatPrice(order.total)}</td>
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
          `/admin/orders${buildQuery({ q: search, status, page: target > 1 ? target : undefined })}`
        }
      />
    </div>
  );
}
