import { formatDate, formatPrice } from '@/lib/format';
import { statusLabel } from '@/lib/orders';
import type { Order } from '@/types/api';

export function AccountOrders({ orders }: { orders: Order[] }) {
  if (orders.length === 0) {
    return <p className="text-sm">You have not placed any orders yet.</p>;
  }

  return (
    <ul className="divide-border border-border divide-y border-y">
      {orders.map((order) => (
        <li key={order.reference} className="space-y-2 py-5 text-sm">
          <div className="flex flex-wrap items-center justify-between gap-2">
            <span className="font-medium">{order.reference}</span>
            <span className="border-border rounded-sm border px-2 py-1 text-xs">
              {statusLabel(order.status)}
            </span>
          </div>
          <p className="text-muted text-xs">{formatDate(order.createdAt)}</p>
          <ul className="space-y-1">
            {order.lines.map((line) => (
              <li key={`${line.productId}-${line.size}`}>
                {line.name} ({line.size}) × {line.quantity}
              </li>
            ))}
          </ul>
          <p className="font-medium">{formatPrice(order.total)}</p>
        </li>
      ))}
    </ul>
  );
}
