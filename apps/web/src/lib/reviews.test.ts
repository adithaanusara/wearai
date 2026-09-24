import { describe, expect, it } from 'vitest';
import type { Review } from '@/data/reviews';
import { averageRating, getReviews } from '@/lib/reviews';

const review = (rating: Review['rating']): Review => ({
  id: String(rating),
  styleId: 's',
  rating,
  title: '',
  body: '',
  author: '',
  date: '2026-01-01',
});

describe('averageRating', () => {
  it('returns null without reviews', () => {
    expect(averageRating([])).toBeNull();
  });

  it('rounds to one decimal', () => {
    expect(averageRating([review(5), review(4), review(4)])).toBe(4.3);
    expect(averageRating([review(5), review(4)])).toBe(4.5);
  });
});

describe('getReviews', () => {
  it('returns reviews for a style only', () => {
    const found = getReviews('essential-fitted-tee');
    expect(found.length).toBeGreaterThan(0);
    expect(found.every((item) => item.styleId === 'essential-fitted-tee')).toBe(true);
    expect(getReviews('unknown')).toEqual([]);
  });
});
