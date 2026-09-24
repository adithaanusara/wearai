export const hero = {
  headline: 'Built for the way you move',
  subtitle: 'New season performance and everyday wear, designed to last.',
  image: '/images/placeholder-alt.svg',
};

export const promo = {
  headline: 'Season sale',
  text: 'Up to 30% off selected styles while stock lasts.',
  cta: { label: 'Shop now', href: '/collections/last-chance' },
  image: '/images/placeholder.svg',
};

interface Tile {
  title: string;
  href: string;
  image: string;
}

const placeholder = '/images/placeholder.svg';

export const categoryBlocks: { title: string; href: string; tiles: Tile[] }[] = [
  {
    title: 'Women',
    href: '/collections/women',
    tiles: [
      { title: 'T-Shirts', href: '/collections/women-t-shirts', image: placeholder },
      { title: 'Leggings', href: '/collections/women-leggings', image: placeholder },
      { title: 'Hoodies', href: '/collections/women-hoodies', image: placeholder },
      { title: 'Shorts', href: '/collections/women-shorts', image: placeholder },
    ],
  },
  {
    title: 'Men',
    href: '/collections/men',
    tiles: [
      { title: 'T-Shirts', href: '/collections/men-t-shirts', image: placeholder },
      { title: 'Shorts', href: '/collections/men-shorts', image: placeholder },
      { title: 'Hoodies', href: '/collections/men-hoodies', image: placeholder },
      { title: 'Joggers', href: '/collections/men-joggers', image: placeholder },
    ],
  },
];

const activityNames = ['Lifting', 'Running', 'Rest Day', 'Casual'];

function activityTiles(gender: 'men' | 'women'): Tile[] {
  return activityNames.map((name) => ({
    title: name,
    href: `/collections/${gender}?activity=${name.toLowerCase().replace(/\s+/g, '-')}`,
    image: placeholder,
  }));
}

export const activities = [
  { id: 'men', label: 'Men', tiles: activityTiles('men') },
  { id: 'women', label: 'Women', tiles: activityTiles('women') },
];
