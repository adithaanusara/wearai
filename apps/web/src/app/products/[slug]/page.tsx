import type { Metadata } from 'next';
import Image from 'next/image';
import { notFound } from 'next/navigation';
import { ColourSwatches } from '@/components/product/ColourSwatches';
import { Container } from '@/components/ui/Container';
import { Stars } from '@/components/ui/Stars';
import { formatPrice } from '@/lib/format';
import { getColourways, getProductBySlug } from '@/lib/products';
import { averageRating, getReviews } from '@/lib/reviews';

interface ProductPageProps {
  params: Promise<{ slug: string }>;
}

export async function generateMetadata({ params }: ProductPageProps): Promise<Metadata> {
  const { slug } = await params;
  const product = getProductBySlug(slug);
  return product
    ? { title: `${product.name} – ${product.colour}`, description: product.description }
    : { title: 'Product not found' };
}

export default async function ProductPage({ params }: ProductPageProps) {
  const { slug } = await params;
  const product = getProductBySlug(slug);
  if (!product) notFound();

  const colourways = getColourways(product);
  const reviews = getReviews(product.styleId);
  const rating = averageRating(reviews);

  return (
    <Container className="py-8 md:py-12">
      <div className="grid gap-8 lg:grid-cols-[1fr_28rem] lg:gap-16">
        <div className="bg-surface relative aspect-4/5">
          <Image
            src={product.images[0]}
            alt={`${product.name} in ${product.colour}`}
            fill
            priority
            sizes="(min-width: 1024px) 50vw, 100vw"
            className="object-cover"
          />
        </div>

        <div className="space-y-8">
          <div>
            {rating !== null && (
              <a href="#reviews" className="mb-3 flex items-center gap-2 text-sm">
                <Stars rating={rating} />
                <span className="underline">
                  {rating} ({reviews.length} {reviews.length === 1 ? 'review' : 'reviews'})
                </span>
              </a>
            )}
            <h1 className="text-2xl font-bold tracking-wide uppercase md:text-3xl">
              {product.name}
            </h1>
            <p className="mt-3 text-lg">
              {product.compareAtPrice !== undefined && (
                <s className="text-muted mr-2">{formatPrice(product.compareAtPrice)}</s>
              )}
              {formatPrice(product.price)}
            </p>
            <p className="text-muted mt-1 text-xs">Tax included.</p>
          </div>

          <ColourSwatches current={product} colourways={colourways} />

          <div className="space-y-4 text-sm">
            <p>{product.description}</p>
            <ul className="list-disc space-y-1 pl-5">
              {product.details.map((detail) => (
                <li key={detail}>{detail}</li>
              ))}
            </ul>
          </div>
        </div>
      </div>
    </Container>
  );
}
