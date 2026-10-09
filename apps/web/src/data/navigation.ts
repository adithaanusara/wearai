import { unsplash } from '@/data/photos';

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
      ],
      tiles: [
        {
          title: 'New Arrivals',
          href: '/collections/women-new',
          image: unsplash('1643834068973-903e3c260269'),
        },
        {
          title: 'Leggings',
          href: '/collections/women-leggings',
          image: unsplash('1762331655528-4af4bccf7c62'),
        },
        {
          title: 'Hoodies',
          href: '/collections/women-hoodies',
          image: unsplash('1620799140188-3b2a02fd9a77'),
        },
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
      ],
      tiles: [
        {
          title: 'New Arrivals',
          href: '/collections/men-new',
          image: unsplash('1677538537484-324385aff147'),
        },
        {
          title: 'T-Shirts',
          href: '/collections/men-t-shirts',
          image: unsplash('1571455786673-9d9d6c194f90'),
        },
        {
          title: 'Joggers',
          href: '/collections/men-joggers',
          image: unsplash('1506629082955-511b1aa562c8'),
        },
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
        { title: 'Bags', href: '/collections/bags', image: unsplash('1699319656128-6e353d6b9c7c') },
        { title: 'Caps', href: '/collections/caps', image: unsplash('1737666636073-f15d9762cf83') },
      ],
    },
  },
  { label: 'Last Chance', href: '/collections/last-chance' },
  { label: 'Gift Cards', href: '/gift-cards' },
];
