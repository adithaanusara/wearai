import type { Metadata } from 'next';
import { getAdminDashboard } from '@/lib/api';
import { statusLabel } from '@/lib/orders';
import { requireRole, serverAuthHeaders } from '@/lib/server-session';

export const metadata: Metadata = { title: 'Dashboard' };

export default async function AdminDashboardPage() {
  await requireRole('staff');
  const dashboard = await getAdminDashboard(await serverAuthHeaders());

  const facts = [
    { label: 'Products', value: dashboard.products },
    { label: 'Customers', value: dashboard.customers },
  ];

  return (
    <div className="space-y-10">
      <h1 className="text-3xl font-bold tracking-wide uppercase">Dashboard</h1>

      <section aria-labelledby="orders-title">
        <h2 id="orders-title" className="mb-4 text-sm font-medium tracking-wide uppercase">
          Orders by status
        </h2>
        <dl className="grid grid-cols-2 gap-4 sm:grid-cols-3 lg:grid-cols-5">
          {Object.entries(dashboard.ordersByStatus).map(([status, count]) => (
            <div key={status} className="border-border rounded-sm border p-4">
              <dt className="text-muted text-xs">{statusLabel(status)}</dt>
              <dd className="mt-1 text-2xl font-bold">{count}</dd>
            </div>
          ))}
        </dl>
      </section>

      <section aria-labelledby="store-title">
        <h2 id="store-title" className="mb-4 text-sm font-medium tracking-wide uppercase">
          Store
        </h2>
        <dl className="grid grid-cols-2 gap-4 sm:grid-cols-3 lg:grid-cols-5">
          {facts.map((fact) => (
            <div key={fact.label} className="border-border rounded-sm border p-4">
              <dt className="text-muted text-xs">{fact.label}</dt>
              <dd className="mt-1 text-2xl font-bold">{fact.value}</dd>
            </div>
          ))}
        </dl>
      </section>
    </div>
  );
}
