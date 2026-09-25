import type { Metadata } from 'next';
import { PolicyPage } from '@/components/layout/PolicyPage';
import { ButtonLink } from '@/components/ui/ButtonLink';

export const metadata: Metadata = { title: 'Gift cards' };

export default function GiftCardsPage() {
  return (
    <PolicyPage title="Gift cards">
      <p>
        Gift cards are coming soon. Check back shortly, or get in touch and we will help you arrange
        one.
      </p>
      <ButtonLink href="/contact">Contact us</ButtonLink>
    </PolicyPage>
  );
}
