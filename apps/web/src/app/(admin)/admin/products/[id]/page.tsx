import type { Metadata } from 'next';
import Image from 'next/image';
import Link from 'next/link';
import { ProductAdminPanel } from '@/components/admin/ProductAdminPanel';
import { hasRole } from '@/lib/admin';
import { getAdminProduct, orNotFound } from '@/lib/api';
import { formatPrice } from '@/lib/format';
import { requireRole, serverAuthHeaders } from '@/lib/server-session';

export const metadata: Metadata = { title: 'Product' };

const sectionTitle = 'mb-4 text-sm font-medium tracking-wide uppercase';

export default async function AdminProductPage({ params }: { params: Promise<{ id: string }> }) {
  const user = await requireRole('staff');
  const { id } = await params;
  const product = await orNotFound(getAdminProduct(id, await serverAuthHeaders()));
  const canEdit = hasRole(user.role, 'admin');

  return (
    <div className="max-w-3xl space-y-10">
      <div>
        <Link href="/admin/products" className="text-muted text-xs underline">
          All products
        </Link>
        <h1 className="mt-2 text-3xl font-bold tracking-wide uppercase">{product.name}</h1>
        <p className="text-muted mt-1 text-sm">
          {product.id} &middot; {product.colour} &middot;{' '}
          <span className="border-border rounded-sm border px-2 py-1 text-xs">
            {product.archived ? 'Archived' : 'In the shop'}
          </span>
        </p>
      </div>

      <div className="flex flex-col gap-6 sm:flex-row">
        {product.image && (
          <div className="bg-surface relative aspect-4/5 w-40 shrink-0 overflow-hidden">
            <Image src={product.image} alt="" fill sizes="160px" className="object-cover" />
          </div>
        )}
        <dl className="space-y-3 text-sm">
          <div>
            <dt className="text-muted text-xs">Category</dt>
            <dd>
              {product.category} ({product.gender})
            </dd>
          </div>
          <div>
            <dt className="text-muted text-xs">Sizes</dt>
            <dd>{product.sizes.join(', ')}</dd>
          </div>
          <div>
            <dt className="text-muted text-xs">Address in the shop</dt>
            <dd className="break-all">/products/{product.slug}</dd>
          </div>
        </dl>
      </div>

      {canEdit ? (
        <ProductAdminPanel product={product} />
      ) : (
        <section aria-labelledby="details-title">
          <h2 id="details-title" className={sectionTitle}>
            Details
          </h2>
          <dl className="space-y-3 text-sm">
            <div>
              <dt className="text-muted text-xs">Price</dt>
              <dd>
                {formatPrice(product.price)}
                {product.compareAtPrice !== null && (
                  <span className="text-muted ml-2 line-through">
                    {formatPrice(product.compareAtPrice)}
                  </span>
                )}
              </dd>
            </div>
            <div>
              <dt className="text-muted text-xs">Description</dt>
              <dd className="whitespace-pre-line">{product.description}</dd>
            </div>
          </dl>
          <p className="text-muted mt-6 text-sm">Only admins can edit or archive products.</p>
        </section>
      )}
    </div>
  );
}
