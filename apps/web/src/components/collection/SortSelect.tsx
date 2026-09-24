'use client';

import { useQueryUpdater } from '@/components/collection/useQueryUpdater';
import { sortOptions, type SortKey } from '@/lib/collection';

export function SortSelect({ value }: { value: SortKey }) {
  const { update } = useQueryUpdater();

  return (
    <label className="flex items-center gap-2 text-xs font-medium tracking-wide uppercase">
      Sort by
      <select
        value={value}
        className="border-border bg-bg rounded-sm border px-3 py-2 text-sm font-normal normal-case"
        onChange={(event) =>
          update((params) => {
            if (event.target.value === 'featured') params.delete('sort');
            else params.set('sort', event.target.value);
          })
        }
      >
        {sortOptions.map((option) => (
          <option key={option.value} value={option.value}>
            {option.label}
          </option>
        ))}
      </select>
    </label>
  );
}
