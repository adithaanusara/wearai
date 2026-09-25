'use client';

import { useRouter } from 'next/navigation';
import { useEffect, useRef } from 'react';
import { useSession } from '@/components/account/SessionProvider';
import { mockOrders } from '@/data/orders';
import { formatDate, formatPrice } from '@/lib/format';
import { useHydrated } from '@/lib/use-hydrated';

const sectionTitle = 'mb-4 text-sm font-medium tracking-wide uppercase';

export function AccountView() {
  const router = useRouter();
  const { session, signOut } = useSession();
  const hydrated = useHydrated();
  const signingOut = useRef(false);

  // The demo session lives in the browser, so the redirect happens here. Real auth can do it on the server.
  useEffect(() => {
    if (hydrated && !session && !signingOut.current) router.replace('/login');
  }, [hydrated, session, router]);

  if (!hydrated || !session) return <div className="min-h-64" aria-hidden="true" />;

  function onSignOut() {
    // Without this, the redirect above would send the visitor to the login page instead of home.
    signingOut.current = true;
    signOut();
    router.push('/');
  }

  return (
    <div className="mt-8 space-y-12">
      <p className="text-sm">Welcome back, {session.name}.</p>

      <section aria-labelledby="orders-title">
        <h2 id="orders-title" className={sectionTitle}>
          Orders
        </h2>
        <ul className="divide-border border-border divide-y border-y">
          {mockOrders.map((order) => (
            <li key={order.reference} className="space-y-2 py-5 text-sm">
              <div className="flex flex-wrap items-center justify-between gap-2">
                <span className="font-medium">{order.reference}</span>
                <span className="border-border rounded-sm border px-2 py-1 text-xs">
                  {order.status}
                </span>
              </div>
              <p className="text-muted text-xs">{formatDate(order.date)}</p>
              <ul className="space-y-1">
                {order.items.map((item) => (
                  <li key={item}>{item}</li>
                ))}
              </ul>
              <p className="font-medium">{formatPrice(order.total)}</p>
            </li>
          ))}
        </ul>
        <p className="text-muted mt-3 text-xs">Sample orders shown for the demo.</p>
      </section>

      <section aria-labelledby="profile-title">
        <h2 id="profile-title" className={sectionTitle}>
          Profile
        </h2>
        <dl className="space-y-3 text-sm">
          <div>
            <dt className="text-muted text-xs">Name</dt>
            <dd>{session.name}</dd>
          </div>
          <div>
            <dt className="text-muted text-xs">Email</dt>
            <dd>{session.email}</dd>
          </div>
        </dl>
      </section>

      <button
        type="button"
        className="border-text hover:bg-surface rounded-sm border px-8 py-3 text-xs font-medium tracking-wide uppercase transition-colors"
        onClick={onSignOut}
      >
        Sign out
      </button>
    </div>
  );
}
