import type { Metadata } from 'next';
import Link from 'next/link';
import { OrderStatusActions } from '@/components/admin/OrderStatusActions';
import { getAdminOrder, orNotFound } from '@/lib/api';
import { formatDate, formatDateTime, formatPrice } from '@/lib/format';
import { statusLabel } from '@/lib/orders';
import { requireRole, serverAuthHeaders } from '@/lib/server-session';

export const metadata: Metadata = { title: 'Order' };

const sectionTitle = 'mb-4 text-sm font-medium tracking-wide uppercase';

export default async function AdminOrderPage({
  params,
}: {
  params: Promise<{ reference: string }>;
}) {
  await requireRole('staff');
  const { reference } = await params;
  const order = await orNotFound(getAdminOrder(reference, await serverAuthHeaders()));

  return (
    <div className="max-w-3xl space-y-10">
      <div>
        <Link href="/admin/orders" className="text-muted text-xs underline">
          All orders
        </Link>
        <h1 className="mt-2 text-3xl font-bold tracking-wide uppercase">{order.reference}</h1>
        <p className="text-muted mt-1 text-sm">
          Placed {formatDate(order.createdAt)} &middot;{' '}
          <span className="border-border rounded-sm border px-2 py-1 text-xs">
            {statusLabel(order.status)}
          </span>
        </p>
      </div>

      <section aria-labelledby="actions-title">
        <h2 id="actions-title" className={sectionTitle}>
          Status
        </h2>
        <OrderStatusActions
          reference={order.reference}
          status={order.status}
          allowedNext={order.allowedNext}
        />
      </section>

      <section aria-labelledby="items-title">
        <h2 id="items-title" className={sectionTitle}>
          Items
        </h2>
        <ul className="divide-border border-border divide-y border-y text-sm">
          {order.lines.map((line) => (
            <li key={`${line.productId}-${line.size}`} className="flex justify-between gap-4 py-3">
              <span>
                {line.name} ({line.colour}, {line.size}) × {line.quantity}
              </span>
              <span className="whitespace-nowrap">{formatPrice(line.lineTotal)}</span>
            </li>
          ))}
        </ul>
        <dl className="mt-4 space-y-1 text-sm">
          <div className="flex justify-between">
            <dt className="text-muted">Subtotal</dt>
            <dd>{formatPrice(order.subtotal)}</dd>
          </div>
          <div className="flex justify-between">
            <dt className="text-muted">Shipping ({order.deliveryMethod})</dt>
            <dd>{formatPrice(order.shipping)}</dd>
          </div>
          <div className="flex justify-between font-medium">
            <dt>Total</dt>
            <dd>{formatPrice(order.total)}</dd>
          </div>
        </dl>
      </section>

      <section aria-labelledby="customer-title">
        <h2 id="customer-title" className={sectionTitle}>
          Customer
        </h2>
        <dl className="space-y-3 text-sm">
          <div>
            <dt className="text-muted text-xs">Name</dt>
            <dd>{order.fullName}</dd>
          </div>
          <div>
            <dt className="text-muted text-xs">Email</dt>
            <dd className="break-all">{order.email}</dd>
          </div>
          <div>
            <dt className="text-muted text-xs">Phone</dt>
            <dd>{order.phone}</dd>
          </div>
          <div>
            <dt className="text-muted text-xs">Delivery address</dt>
            <dd>
              {[order.address1, order.address2, order.city, order.district, order.province]
                .filter(Boolean)
                .join(', ')}{' '}
              {order.postalCode}
            </dd>
          </div>
          <div>
            <dt className="text-muted text-xs">Payment</dt>
            <dd>{order.paymentMethod}</dd>
          </div>
        </dl>
      </section>

      <section aria-labelledby="history-title">
        <h2 id="history-title" className={sectionTitle}>
          History
        </h2>
        {order.history.length === 0 ? (
          <p className="text-muted text-sm">No status changes yet.</p>
        ) : (
          <ol className="divide-border border-border divide-y border-y text-sm">
            {order.history.map((change) => (
              <li key={`${change.createdAt}-${change.toStatus}`} className="space-y-1 py-3">
                <p>
                  {statusLabel(change.fromStatus)} → {statusLabel(change.toStatus)}
                </p>
                <p className="text-muted text-xs">
                  {change.actorEmail} &middot;{' '}
                  <time dateTime={change.createdAt}>{formatDateTime(change.createdAt)}</time>
                </p>
              </li>
            ))}
          </ol>
        )}
      </section>
    </div>
  );
}
