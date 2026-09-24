import { siteConfig } from '@/config/site';

const numberFormat = new Intl.NumberFormat('en-US', {
  minimumFractionDigits: 2,
  maximumFractionDigits: 2,
});

/** Formats a whole-rupee amount as `LKR 4,450.00`. */
export function formatPrice(amount: number): string {
  return `${siteConfig.currency} ${numberFormat.format(amount)}`;
}

const dateFormat = new Intl.DateTimeFormat('en-GB', {
  day: 'numeric',
  month: 'long',
  year: 'numeric',
  timeZone: 'UTC',
});

/** Formats an ISO date such as 2026-09-12 as "12 September 2026". */
export function formatDate(isoDate: string): string {
  return dateFormat.format(new Date(isoDate));
}
