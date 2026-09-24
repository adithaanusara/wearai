'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { useQueryUpdater } from '@/components/collection/useQueryUpdater';
import { hasActiveFilters, type CollectionFilters, type FilterOptions } from '@/lib/collection';

interface FilterPanelProps {
  options: FilterOptions;
  filters: CollectionFilters;
}

const legendClass = 'mb-3 text-xs font-medium tracking-wide uppercase';
const inputClass = 'border-border w-full rounded-sm border px-3 py-2 text-sm';

export function FilterPanel({ options, filters }: FilterPanelProps) {
  const pathname = usePathname();
  const { update, queryKey } = useQueryUpdater();

  function toggle(key: 'size' | 'colour', value: string) {
    update((params) => {
      const current = params.getAll(key);
      params.delete(key);
      const next = current.includes(value)
        ? current.filter((item) => item !== value)
        : [...current, value];
      next.forEach((item) => params.append(key, item));
    });
  }

  function setPrice(key: 'min' | 'max', value: string) {
    update((params) => {
      if (value === '') params.delete(key);
      else params.set(key, value);
    });
  }

  return (
    <div className="space-y-8">
      <fieldset>
        <legend className={legendClass}>Size</legend>
        <div className="flex flex-wrap gap-2">
          {options.sizes.map((size) => (
            <label key={size} className="cursor-pointer">
              <input
                type="checkbox"
                className="peer sr-only"
                checked={filters.sizes.includes(size)}
                onChange={() => toggle('size', size)}
              />
              <span className="border-border peer-checked:bg-text peer-checked:text-bg peer-checked:border-text peer-focus-visible:outline-text block rounded-sm border px-3 py-2 text-xs peer-focus-visible:outline-2 peer-focus-visible:outline-offset-2">
                {size}
              </span>
            </label>
          ))}
        </div>
      </fieldset>

      <fieldset>
        <legend className={legendClass}>Colour</legend>
        <ul className="space-y-2">
          {options.colours.map((colour) => (
            <li key={colour}>
              <label className="flex cursor-pointer items-center gap-3 text-sm">
                <input
                  type="checkbox"
                  className="accent-text h-4 w-4"
                  checked={filters.colours.includes(colour)}
                  onChange={() => toggle('colour', colour)}
                />
                {colour}
              </label>
            </li>
          ))}
        </ul>
      </fieldset>

      {/* Keyed by the query string so the fields reset when filters are cleared. */}
      <fieldset key={queryKey}>
        <legend className={legendClass}>Price (LKR)</legend>
        <div className="flex items-center gap-2">
          <label className="flex-1">
            <span className="sr-only">Minimum price</span>
            <input
              type="number"
              inputMode="numeric"
              min={0}
              placeholder={String(options.minPrice)}
              defaultValue={filters.minPrice ?? ''}
              className={inputClass}
              onBlur={(event) => setPrice('min', event.target.value)}
              onKeyDown={(event) => event.key === 'Enter' && event.currentTarget.blur()}
            />
          </label>
          <span aria-hidden="true">–</span>
          <label className="flex-1">
            <span className="sr-only">Maximum price</span>
            <input
              type="number"
              inputMode="numeric"
              min={0}
              placeholder={String(options.maxPrice)}
              defaultValue={filters.maxPrice ?? ''}
              className={inputClass}
              onBlur={(event) => setPrice('max', event.target.value)}
              onKeyDown={(event) => event.key === 'Enter' && event.currentTarget.blur()}
            />
          </label>
        </div>
      </fieldset>

      {hasActiveFilters(filters) && (
        <Link href={pathname} scroll={false} className="inline-block text-sm underline">
          Clear all filters
        </Link>
      )}
    </div>
  );
}
