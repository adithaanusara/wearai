import Image from 'next/image';
import Link from 'next/link';
import { formatPrice } from '@/lib/format';
import type { Product } from '@/types/product';

interface ProductCardProps {
  product: Product;
  /** Value for the `sizes` attribute, matching how wide the card renders. */
  imageSizes?: string;
}

export function ProductCard({
  product,
  imageSizes = '(min-width: 1024px) 25vw, 50vw',
}: ProductCardProps) {
  const [primary, secondary] = product.images;

  return (
    <article className="group relative">
      <div className="bg-surface relative aspect-4/5 overflow-hidden">
        <Image
          src={primary}
          alt={`${product.name} in ${product.colour}`}
          fill
          sizes={imageSizes}
          className="object-cover"
        />
        <Image
          src={secondary}
          alt=""
          fill
          sizes={imageSizes}
          className="object-cover opacity-0 transition-opacity duration-300 group-focus-within:opacity-100 group-hover:opacity-100"
        />
        {product.isNew && (
          <span className="bg-bg text-text absolute top-3 left-3 px-2 py-1 text-[10px] font-medium tracking-wide uppercase">
            New
          </span>
        )}
      </div>

      <div className="mt-3 space-y-1">
        <h3 className="text-sm font-medium">
          {/* The stretched link makes the whole card clickable and focusable. */}
          <Link href={`/products/${product.slug}`} className="after:absolute after:inset-0">
            {product.name}
          </Link>
        </h3>
        <p className="text-muted text-sm">{product.colour}</p>
        <p className="text-sm">
          {product.compareAtPrice !== undefined && (
            <s className="text-muted mr-2">{formatPrice(product.compareAtPrice)}</s>
          )}
          {formatPrice(product.price)}
        </p>
      </div>
    </article>
  );
}
