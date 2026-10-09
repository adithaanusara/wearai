import { unsplash } from '@/data/photos';

export const hero = {
  headline: 'Built for the way you move',
  subtitle: 'New season performance and everyday wear, designed to last.',
  image: unsplash('1554284126-aa88f22d8b74', 2000),
};

export const promo = {
  headline: 'Season sale',
  text: 'Up to 30% off selected styles while stock lasts.',
  cta: { label: 'Shop now', href: '/collections/last-chance' },
  image: unsplash('1766934587163-186d20bf3d40', 2000),
};

interface Tile {
  title: string;
  href: string;
  image: string;
}

export const categoryBlocks: { title: string; href: string; tiles: Tile[] }[] = [
  {
    title: 'Women',
    href: '/collections/women',
    tiles: [
      {
        title: 'T-Shirts',
        href: '/collections/women-t-shirts',
        image: unsplash('1651761179569-4ba2aa054997'),
      },
      {
        title: 'Leggings',
        href: '/collections/women-leggings',
        image: unsplash('1626026397008-3316047db4fc'),
      },
      {
        title: 'Hoodies',
        href: '/collections/women-hoodies',
        image: unsplash('1620799140188-3b2a02fd9a77'),
      },
      {
        title: 'Shorts',
        href: '/collections/women-shorts',
        image: unsplash('1789110519888-758d7ab3908e'),
      },
    ],
  },
  {
    title: 'Men',
    href: '/collections/men',
    tiles: [
      {
        title: 'T-Shirts',
        href: '/collections/men-t-shirts',
        image: unsplash('1521572163474-6864f9cf17ab'),
      },
      {
        title: 'Shorts',
        href: '/collections/men-shorts',
        image: unsplash('1600878585887-c2b9530999a1'),
      },
      {
        title: 'Hoodies',
        href: '/collections/men-hoodies',
        image: unsplash('1673092147872-5ddb03194341'),
      },
      {
        title: 'Joggers',
        href: '/collections/men-joggers',
        image: unsplash('1789110854262-ec66f0648ec7'),
      },
    ],
  },
];

const activityPhotos: Record<'men' | 'women', Record<string, string>> = {
  men: {
    Lifting: '1598971475122-95a9004e2922',
    Running: '1633394443693-8b930f9889bc',
    'Rest Day': '1611817757591-c3f345024273',
    Casual: '1664700684960-3e27ef397f8f',
  },
  women: {
    Lifting: '1772450014048-ec6dc611be2b',
    Running: '1616466137547-c3e1d511a033',
    'Rest Day': '1759229874786-6d0cc75d95be',
    Casual: '1590330297626-d7aff25a0431',
  },
};

function activityTiles(gender: 'men' | 'women'): Tile[] {
  return Object.entries(activityPhotos[gender]).map(([name, photo]) => ({
    title: name,
    href: `/collections/${gender}?activity=${name.toLowerCase().replace(/\s+/g, '-')}`,
    image: unsplash(photo),
  }));
}

export const activities = [
  { id: 'men', label: 'Men', tiles: activityTiles('men') },
  { id: 'women', label: 'Women', tiles: activityTiles('women') },
];
