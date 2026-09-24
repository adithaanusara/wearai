export interface NavLink {
  label: string;
  href: string;
}

export interface NavTile {
  title: string;
  href: string;
  image: string;
}

export interface NavMenu {
  featured: NavLink[];
  explore: NavLink[];
  tiles: NavTile[];
}

export interface NavItem extends NavLink {
  menu?: NavMenu;
}

const placeholder = '/images/placeholder.svg';

export const mainNav: NavItem[] = [
  {
    label: 'Women',
    href: '/collections/women',
    menu: {
      featured: [
        { label: 'New Arrivals', href: '/collections/women-new' },
        { label: 'Best Sellers', href: '/collections/women-best-sellers' },
        { label: 'Shop All', href: '/collections/women' },
      ],
      explore: [
        { label: 'T-Shirts', href: '/collections/women-t-shirts' },
        { label: 'Leggings', href: '/collections/women-leggings' },
        { label: 'Hoodies', href: '/collections/women-hoodies' },
        { label: 'Shorts', href: '/collections/women-shorts' },
        { label: 'Sports Bras', href: '/collections/women-sports-bras' },
      ],
      tiles: [
        { title: 'New Arrivals', href: '/collections/women-new', image: placeholder },
        { title: 'Leggings', href: '/collections/women-leggings', image: placeholder },
        { title: 'Hoodies', href: '/collections/women-hoodies', image: placeholder },
      ],
    },
  },
  {
    label: 'Men',
    href: '/collections/men',
    menu: {
      featured: [
        { label: 'New Arrivals', href: '/collections/men-new' },
        { label: 'Best Sellers', href: '/collections/men-best-sellers' },
        { label: 'Shop All', href: '/collections/men' },
      ],
      explore: [
        { label: 'T-Shirts', href: '/collections/men-t-shirts' },
        { label: 'Shorts', href: '/collections/men-shorts' },
        { label: 'Hoodies', href: '/collections/men-hoodies' },
        { label: 'Joggers', href: '/collections/men-joggers' },
        { label: 'Tank Tops', href: '/collections/men-tank-tops' },
      ],
      tiles: [
        { title: 'New Arrivals', href: '/collections/men-new', image: placeholder },
        { title: 'T-Shirts', href: '/collections/men-t-shirts', image: placeholder },
        { title: 'Joggers', href: '/collections/men-joggers', image: placeholder },
      ],
    },
  },
  {
    label: 'Accessories',
    href: '/collections/accessories',
    menu: {
      featured: [
        { label: 'New Arrivals', href: '/collections/accessories-new' },
        { label: 'Shop All', href: '/collections/accessories' },
      ],
      explore: [
        { label: 'Bags', href: '/collections/bags' },
        { label: 'Caps', href: '/collections/caps' },
        { label: 'Socks', href: '/collections/socks' },
        { label: 'Bottles', href: '/collections/bottles' },
      ],
      tiles: [
        { title: 'Bags', href: '/collections/bags', image: placeholder },
        { title: 'Caps', href: '/collections/caps', image: placeholder },
      ],
    },
  },
  { label: 'Last Chance', href: '/collections/last-chance' },
  { label: 'Gift Cards', href: '/gift-cards' },
];
