import Image from 'next/image';
import Link from 'next/link';
import { formatPrice } from '@/lib/format';
import type { Product } from '@/types/product';

interface ChatProductCardProps {
  product: Product;
  onNavigate: () => void;
}

/** A compact product row that fits inside a chat bubble. */
export function ChatProductCard({ product, onNavigate }: ChatProductCardProps) {
  return (
    <Link
      href={`/products/${product.slug}`}
      onClick={onNavigate}
      className="border-border bg-bg flex items-center gap-3 rounded-sm border p-2 hover:bg-surface"
    >
      <span className="bg-surface relative block h-16 w-12 shrink-0">
        <Image
          src={product.images[0]}
          alt={`${product.name} in ${product.colour}`}
          fill
          sizes="48px"
          className="object-cover"
        />
      </span>
      <span className="min-w-0 text-sm">
        <span className="block truncate font-medium">{product.name}</span>
        <span className="text-muted block text-xs">{product.colour}</span>
        <span className="block">{formatPrice(product.price)}</span>
      </span>
    </Link>
  );
}
