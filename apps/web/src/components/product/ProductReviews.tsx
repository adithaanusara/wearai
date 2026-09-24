import { Stars } from '@/components/ui/Stars';
import type { Review } from '@/data/reviews';

interface ProductReviewsProps {
  reviews: Review[];
  rating: number | null;
}

const dateFormat = new Intl.DateTimeFormat('en-GB', {
  day: 'numeric',
  month: 'long',
  year: 'numeric',
  timeZone: 'UTC',
});

export function ProductReviews({ reviews, rating }: ProductReviewsProps) {
  return (
    <section id="reviews" aria-labelledby="reviews-title" className="scroll-mt-24">
      <h2 id="reviews-title" className="text-xl font-bold tracking-wide uppercase">
        Reviews
      </h2>

      {rating === null ? (
        <p className="text-muted mt-4 text-sm">No reviews yet.</p>
      ) : (
        <>
          <p className="mt-3 flex items-center gap-2 text-sm">
            <Stars rating={rating} />
            <span>
              {rating} out of 5 · {reviews.length} {reviews.length === 1 ? 'review' : 'reviews'}
            </span>
          </p>
          <ul className="divide-border mt-6 divide-y">
            {reviews.map((review) => (
              <li key={review.id} className="space-y-2 py-6">
                <Stars rating={review.rating} className="text-sm" />
                <h3 className="text-sm font-medium">{review.title}</h3>
                <p className="text-sm">{review.body}</p>
                <p className="text-muted text-xs">
                  {review.author} · {dateFormat.format(new Date(review.date))}
                </p>
              </li>
            ))}
          </ul>
        </>
      )}
    </section>
  );
}
