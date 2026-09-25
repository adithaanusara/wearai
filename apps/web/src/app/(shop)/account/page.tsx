import type { Metadata } from 'next';
import { redirect } from 'next/navigation';
import { AccountOrders } from '@/components/account/AccountOrders';
import { SignOutButton } from '@/components/account/SignOutButton';
import { Pagination } from '@/components/collection/Pagination';
import { Container } from '@/components/ui/Container';
import { ApiError, buildQuery, getMe, getMyOrders } from '@/lib/api';
import { parsePage, type SearchParams } from '@/lib/collection';
import { serverAuthHeaders } from '@/lib/server-session';

export const metadata: Metadata = { title: 'My account' };

// The page depends on who is asking, so it is checked and rendered on every request.
export const dynamic = 'force-dynamic';

const sectionTitle = 'mb-4 text-sm font-medium tracking-wide uppercase';

export default async function AccountPage({
  searchParams,
}: {
  searchParams: Promise<SearchParams>;
}) {
  const headers = await serverAuthHeaders();
  const user = await getMe(headers);
  // Nobody is signed in: redirect before any of the page is produced.
  if (!user) redirect('/login');

  const page = parsePage(await searchParams);
  let orders;
  try {
    orders = await getMyOrders(page, headers);
  } catch (error) {
    // The session ended between the two requests.
    if (error instanceof ApiError && error.status === 401) redirect('/login');
    throw error;
  }
  const pageCount = Math.max(1, Math.ceil(orders.total / orders.pageSize));

  return (
    <Container className="py-10 md:py-14">
      <h1 className="text-3xl font-bold tracking-wide uppercase md:text-4xl">My account</h1>

      <div className="mt-8 max-w-2xl space-y-12">
        <p className="text-sm">Welcome back, {user.name}.</p>

        <section aria-labelledby="orders-title">
          <h2 id="orders-title" className={sectionTitle}>
            Orders
          </h2>
          <AccountOrders orders={orders.items} />
          <Pagination
            page={page}
            pageCount={pageCount}
            hrefFor={(target) => `/account${buildQuery({ page: target > 1 ? target : undefined })}`}
          />
        </section>

        <section aria-labelledby="profile-title">
          <h2 id="profile-title" className={sectionTitle}>
            Profile
          </h2>
          <dl className="space-y-3 text-sm">
            <div>
              <dt className="text-muted text-xs">Name</dt>
              <dd>{user.name}</dd>
            </div>
            <div>
              <dt className="text-muted text-xs">Email</dt>
              <dd>{user.email}</dd>
            </div>
          </dl>
        </section>

        <SignOutButton />
      </div>
    </Container>
  );
}
