'use client';

import { useState } from 'react';
import { ProductArchiveButton } from '@/components/admin/ProductArchiveButton';
import { ProductEditForm } from '@/components/admin/ProductEditForm';
import { ProductImages } from '@/components/admin/ProductImages';
import type { AdminProduct } from '@/types/api';

export interface Notice {
  text: string;
  kind: 'error' | 'success';
}

const sectionTitle = 'mb-4 text-sm font-medium tracking-wide uppercase';

/**
 * The admin's controls for one product. The message lives here, above the parts that start over
 * whenever the product's version changes, so it is still on screen after the page reloads the
 * newer version (for example after a refused, out-of-date save).
 */
export function ProductAdminPanel({ product }: { product: AdminProduct }) {
  const [notice, setNotice] = useState<Notice | null>(null);

  return (
    <div className="space-y-10">
      {notice && (
        <p
          role={notice.kind === 'error' ? 'alert' : 'status'}
          className={`text-sm ${notice.kind === 'error' ? 'text-error' : 'text-success'}`}
        >
          {notice.text}
        </p>
      )}

      <section aria-labelledby="edit-title">
        <h2 id="edit-title" className={sectionTitle}>
          Details
        </h2>
        {/* A new key after every change makes the form start from the saved values. */}
        <ProductEditForm key={product.updatedAt} product={product} onNotice={setNotice} />
      </section>

      <section aria-labelledby="images-title">
        <h2 id="images-title" className={sectionTitle}>
          Images
        </h2>
        <ProductImages key={product.updatedAt} product={product} onNotice={setNotice} />
      </section>

      <section aria-labelledby="archive-title">
        <h2 id="archive-title" className={sectionTitle}>
          Visibility
        </h2>
        <ProductArchiveButton
          key={product.updatedAt}
          id={product.id}
          updatedAt={product.updatedAt}
          archived={product.archived}
          onNotice={setNotice}
        />
      </section>
    </div>
  );
}
