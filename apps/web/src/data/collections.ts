import type { Category, Gender, Product } from '@/types/product';

export interface Collection {
  slug: string;
  title: string;
  includes: (product: Product) => boolean;
}

const forGender = (gender: Gender) => (product: Product) =>
  product.gender === gender || product.gender === 'unisex';

function genderCollections(gender: 'women' | 'men'): Collection[] {
  const title = gender === 'women' ? 'Women' : 'Men';
  const inGender = forGender(gender);

  const categories: [Category, string][] = [
    ['t-shirts', 'T-Shirts'],
    ['leggings', 'Leggings'],
    ['hoodies', 'Hoodies'],
    ['shorts', 'Shorts'],
    ['joggers', 'Joggers'],
  ];

  return [
    { slug: gender, title, includes: inGender },
    {
      slug: `${gender}-new`,
      title: `${title} New Arrivals`,
      includes: (p) => inGender(p) && p.isNew,
    },
    {
      slug: `${gender}-best-sellers`,
      title: `${title} Best Sellers`,
      includes: (p) => inGender(p) && Boolean(p.isBestSeller),
    },
    ...categories.map(([category, label]) => ({
      slug: `${gender}-${category}`,
      title: `${title} ${label}`,
      includes: (p: Product) => inGender(p) && p.category === category,
    })),
  ];
}

const accessoryCategories: [Category, string][] = [
  ['bags', 'Bags'],
  ['caps', 'Caps'],
  ['socks', 'Socks'],
  ['bottles', 'Bottles'],
];

export const collections: Collection[] = [
  ...genderCollections('women'),
  ...genderCollections('men'),
  {
    slug: 'accessories',
    title: 'Accessories',
    includes: (p) => p.gender === 'unisex',
  },
  {
    slug: 'accessories-new',
    title: 'Accessories New Arrivals',
    includes: (p) => p.gender === 'unisex' && p.isNew,
  },
  ...accessoryCategories.map(([category, title]) => ({
    slug: category,
    title,
    includes: (p: Product) => p.category === category,
  })),
  { slug: 'new', title: 'New Arrivals', includes: (p) => p.isNew },
  {
    slug: 'last-chance',
    title: 'Last Chance',
    includes: (p) => p.compareAtPrice !== undefined,
  },
];

export function getCollection(slug: string): Collection | undefined {
  return collections.find((collection) => collection.slug === slug);
}
