'use client';

import { useState } from 'react';
import { FilterPanel } from '@/components/collection/FilterPanel';
import { Drawer } from '@/components/ui/Drawer';
import type { CollectionFilters, FilterOptions } from '@/lib/collection';

interface FilterDrawerProps {
  options: FilterOptions;
  filters: CollectionFilters;
  resultCount: number;
}

export function FilterDrawer({ options, filters, resultCount }: FilterDrawerProps) {
  const [open, setOpen] = useState(false);

  return (
    <div className="lg:hidden">
      <button
        type="button"
        className="border-border rounded-sm border px-4 py-2 text-xs font-medium tracking-wide uppercase"
        aria-haspopup="dialog"
        onClick={() => setOpen(true)}
      >
        Filters
      </button>

      <Drawer open={open} onClose={() => setOpen(false)} title="Filters" side="left">
        <div className="flex-1 overflow-y-auto px-(--gutter) py-6">
          <FilterPanel options={options} filters={filters} />
        </div>
        <div className="border-border border-t p-(--gutter)">
          <button
            type="button"
            className="bg-text text-bg w-full rounded-sm px-6 py-3 text-xs font-medium tracking-wide uppercase"
            onClick={() => setOpen(false)}
          >
            Show {resultCount} {resultCount === 1 ? 'product' : 'products'}
          </button>
        </div>
      </Drawer>
    </div>
  );
}
