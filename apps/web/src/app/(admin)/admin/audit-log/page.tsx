import type { Metadata } from 'next';
import { notFound } from 'next/navigation';
import { Pagination } from '@/components/collection/Pagination';
import { actionLabel, describeChange } from '@/lib/admin';
import { ApiError, buildQuery, getAuditLog } from '@/lib/api';
import { parsePage, type SearchParams } from '@/lib/collection';
import { formatDateTime } from '@/lib/format';
import { requireRole, serverAuthHeaders } from '@/lib/server-session';

export const metadata: Metadata = { title: 'Audit log' };

export default async function AdminAuditLogPage({
  searchParams,
}: {
  searchParams: Promise<SearchParams>;
}) {
  await requireRole('admin');
  const page = parsePage(await searchParams);

  let log;
  try {
    log = await getAuditLog(page, await serverAuthHeaders());
  } catch (error) {
    if (error instanceof ApiError && (error.status === 401 || error.status === 403)) notFound();
    throw error;
  }
  const pageCount = Math.max(1, Math.ceil(log.total / log.pageSize));

  return (
    <div className="space-y-8">
      <h1 className="text-3xl font-bold tracking-wide uppercase">Audit log</h1>
      <p className="text-muted text-sm">
        Every change made from the admin area, newest first. Entries cannot be edited or deleted.
      </p>

      {log.items.length === 0 ? (
        <p className="text-sm">Nothing has been recorded yet.</p>
      ) : (
        <ul className="divide-border border-border divide-y border-y">
          {log.items.map((entry) => (
            <li key={entry.id} className="space-y-1 py-4 text-sm">
              <div className="flex flex-wrap items-center justify-between gap-2">
                <span className="font-medium">{actionLabel(entry.action)}</span>
                <time dateTime={entry.createdAt} className="text-muted text-xs">
                  {formatDateTime(entry.createdAt)}
                </time>
              </div>
              <p className="text-muted text-xs break-all">By {entry.actorEmail}</p>
              {describeChange(entry.details) && (
                <p className="break-all">{describeChange(entry.details)}</p>
              )}
            </li>
          ))}
        </ul>
      )}

      <Pagination
        page={page}
        pageCount={pageCount}
        hrefFor={(target) =>
          `/admin/audit-log${buildQuery({ page: target > 1 ? target : undefined })}`
        }
      />
    </div>
  );
}
