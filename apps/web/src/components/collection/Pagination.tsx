import Link from 'next/link';

interface PaginationProps {
  page: number;
  pageCount: number;
  /** Builds the link for a page, keeping the current filters. */
  hrefFor: (page: number) => string;
}

const linkClass =
  'border-border hover:bg-surface rounded-sm border px-4 py-2 text-xs font-medium tracking-wide uppercase';

export function Pagination({ page, pageCount, hrefFor }: PaginationProps) {
  if (pageCount <= 1) return null;

  return (
    <nav aria-label="Pagination" className="mt-12 flex items-center justify-center gap-4 text-sm">
      {page > 1 ? (
        <Link href={hrefFor(page - 1)} rel="prev" className={linkClass}>
          Previous
        </Link>
      ) : (
        <span aria-hidden="true" className={`${linkClass} invisible`}>
          Previous
        </span>
      )}
      <span aria-current="page">
        Page {page} of {pageCount}
      </span>
      {page < pageCount ? (
        <Link href={hrefFor(page + 1)} rel="next" className={linkClass}>
          Next
        </Link>
      ) : (
        <span aria-hidden="true" className={`${linkClass} invisible`}>
          Next
        </span>
      )}
    </nav>
  );
}
