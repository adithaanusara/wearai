import type { Metadata } from 'next';
import { Pagination } from '@/components/collection/Pagination';
import { RoleSelect } from '@/components/admin/RoleSelect';
import { ApiError, buildQuery, getAdminUsers } from '@/lib/api';
import { roleLabel, roles } from '@/lib/admin';
import { parsePage, type SearchParams } from '@/lib/collection';
import { formatDate } from '@/lib/format';
import { requireRole, serverAuthHeaders } from '@/lib/server-session';
import { notFound } from 'next/navigation';

export const metadata: Metadata = { title: 'Users' };

const first = (value: string | string[] | undefined) => (Array.isArray(value) ? value[0] : value);

export default async function AdminUsersPage({
  searchParams,
}: {
  searchParams: Promise<SearchParams>;
}) {
  const me = await requireRole('admin');
  const params = await searchParams;
  const page = parsePage(params);
  const search = first(params.q)?.trim().slice(0, 100) || undefined;
  const roleParam = first(params.role);
  const role = roles.find((option) => option === roleParam);

  let users;
  try {
    users = await getAdminUsers({ search, role, page }, await serverAuthHeaders());
  } catch (error) {
    if (error instanceof ApiError && (error.status === 401 || error.status === 403)) notFound();
    throw error;
  }
  const pageCount = Math.max(1, Math.ceil(users.total / users.pageSize));

  return (
    <div className="space-y-8">
      <h1 className="text-3xl font-bold tracking-wide uppercase">Users</h1>

      <form method="get" role="search" className="flex flex-wrap items-end gap-3">
        <div>
          <label htmlFor="user-search" className="text-muted mb-1 block text-xs">
            Name or email
          </label>
          <input
            id="user-search"
            name="q"
            type="search"
            defaultValue={search}
            maxLength={100}
            className="border-border bg-bg w-64 max-w-full rounded-sm border px-3 py-2 text-sm"
          />
        </div>
        <div>
          <label htmlFor="user-role" className="text-muted mb-1 block text-xs">
            Role
          </label>
          <select
            id="user-role"
            name="role"
            defaultValue={role ?? ''}
            className="border-border bg-bg rounded-sm border px-3 py-2 text-sm"
          >
            <option value="">All</option>
            {roles.map((option) => (
              <option key={option} value={option}>
                {roleLabel(option)}
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
        {users.total} {users.total === 1 ? 'user' : 'users'}
      </p>

      {users.items.length === 0 ? (
        <p className="text-sm">No users match.</p>
      ) : (
        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm">
            <caption className="sr-only">Users and their roles</caption>
            <thead className="text-muted text-xs">
              <tr className="border-border border-b">
                <th scope="col" className="py-2 pr-4 font-normal">
                  Name
                </th>
                <th scope="col" className="py-2 pr-4 font-normal">
                  Email
                </th>
                <th scope="col" className="py-2 pr-4 font-normal">
                  Joined
                </th>
                <th scope="col" className="py-2 font-normal">
                  Role
                </th>
              </tr>
            </thead>
            <tbody className="divide-border divide-y">
              {users.items.map((user) => (
                <tr key={user.id}>
                  <td className="py-3 pr-4">{user.name}</td>
                  <td className="py-3 pr-4 break-all">{user.email}</td>
                  <td className="py-3 pr-4 whitespace-nowrap">{formatDate(user.createdAt)}</td>
                  <td className="py-3">
                    <RoleSelect
                      // A new key after a save makes the select show the saved role.
                      key={`${user.id}-${user.role}`}
                      userId={user.id}
                      email={user.email}
                      role={user.role}
                      isSelf={user.id === me.id}
                    />
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
          `/admin/users${buildQuery({ q: search, role, page: target > 1 ? target : undefined })}`
        }
      />
    </div>
  );
}
