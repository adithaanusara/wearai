export interface Review {
  id: string;
  /** Matches Product.styleId, so a review applies to every colour of a style. */
  styleId: string;
  rating: 1 | 2 | 3 | 4 | 5;
  title: string;
  body: string;
  author: string;
  date: string;
}

export const reviews: Review[] = [
  {
    id: 'r1',
    styleId: 'essential-fitted-tee',
    rating: 5,
    title: 'My go-to tee',
    body: 'Soft fabric and a clean fit. I bought a second colour straight away.',
    author: 'Nimali P.',
    date: '2026-08-14',
  },
  {
    id: 'r2',
    styleId: 'essential-fitted-tee',
    rating: 4,
    title: 'Great, runs slightly small',
    body: 'Lovely quality. I would go one size up if you like a looser fit.',
    author: 'Dilani R.',
    date: '2026-08-29',
  },
  {
    id: 'r3',
    styleId: 'seamless-high-rise-leggings',
    rating: 5,
    title: 'Stay put during workouts',
    body: 'No digging in, no see-through, and they hold their shape after washing.',
    author: 'Tharushi S.',
    date: '2026-09-02',
  },
  {
    id: 'r4',
    styleId: 'seamless-high-rise-leggings',
    rating: 4,
    title: 'Very comfortable',
    body: 'Comfortable for long sessions. Wish there were more colour options.',
    author: 'Ishara K.',
    date: '2026-09-10',
  },
  {
    id: 'r5',
    styleId: 'pullover-hoodie',
    rating: 5,
    title: 'Heavy and warm',
    body: 'Thick fleece and a great fit through the shoulders.',
    author: 'Kavindu M.',
    date: '2026-08-21',
  },
  {
    id: 'r6',
    styleId: 'heavyweight-oversized-tee',
    rating: 3,
    title: 'Good, but boxy',
    body: 'Nice fabric. The oversized cut is very roomy, so size down if unsure.',
    author: 'Sandun W.',
    date: '2026-09-05',
  },
  {
    id: 'r7',
    styleId: 'gym-duffel-bag',
    rating: 5,
    title: 'Fits everything',
    body: 'The shoe compartment is a great touch, and the strap is comfortable.',
    author: 'Chamara D.',
    date: '2026-09-12',
  },
];
