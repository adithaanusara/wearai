import { siteConfig } from '@/config/site';

const numberFormat = new Intl.NumberFormat('en-US', {
  minimumFractionDigits: 2,
  maximumFractionDigits: 2,
});

/** Formats a whole-rupee amount as `LKR 4,450.00`. */
export function formatPrice(amount: number): string {
  return `${siteConfig.currency} ${numberFormat.format(amount)}`;
}
