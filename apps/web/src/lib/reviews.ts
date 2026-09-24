import { reviews } from '@/data/reviews';
import type { Review } from '@/data/reviews';

export function getReviews(styleId: string): Review[] {
  return reviews.filter((review) => review.styleId === styleId);
}

/** Average rating rounded to one decimal, or null when there are no reviews. */
export function averageRating(items: Review[]): number | null {
  if (items.length === 0) return null;
  const total = items.reduce((sum, review) => sum + review.rating, 0);
  return Math.round((total / items.length) * 10) / 10;
}
