import type { NavLink } from '@/data/navigation';

export interface SocialLink extends NavLink {
  platform: 'instagram' | 'facebook' | 'tiktok' | 'youtube';
}

export const footerColumns: { title: string; links: NavLink[] }[] = [
  {
    title: 'Shop',
    links: [
      { label: 'Women', href: '/collections/women' },
      { label: 'Men', href: '/collections/men' },
      { label: 'Accessories', href: '/collections/accessories' },
      { label: 'New Arrivals', href: '/collections/new' },
      { label: 'Last Chance', href: '/collections/last-chance' },
    ],
  },
  {
    title: 'Information',
    links: [
      { label: 'FAQ', href: '/faq' },
      { label: 'Returns & Exchanges', href: '/returns' },
      { label: 'Shipping Policy', href: '/shipping' },
      { label: 'Contact', href: '/contact' },
    ],
  },
];

export const socialLinks: SocialLink[] = [
  { platform: 'instagram', label: 'Instagram', href: 'https://instagram.com' },
  { platform: 'facebook', label: 'Facebook', href: 'https://facebook.com' },
  { platform: 'tiktok', label: 'TikTok', href: 'https://tiktok.com' },
  { platform: 'youtube', label: 'YouTube', href: 'https://youtube.com' },
];
