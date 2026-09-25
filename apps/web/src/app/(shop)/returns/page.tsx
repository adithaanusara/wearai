import type { Metadata } from 'next';
import Link from 'next/link';
import { PolicyHeading, PolicyPage } from '@/components/layout/PolicyPage';
import { siteConfig } from '@/config/site';

export const metadata: Metadata = { title: 'Returns & exchanges' };

export default function ReturnsPage() {
  const { windowDays } = siteConfig.returns;

  return (
    <PolicyPage title="Returns & exchanges">
      <p>
        If something is not right, you can return or exchange it within {windowDays} days of
        receiving your order.
      </p>

      <PolicyHeading>What can be returned</PolicyHeading>
      <ul className="list-disc space-y-2 pl-5">
        <li>Items must be unworn, unwashed and in their original condition.</li>
        <li>Original tags and packaging should be included.</li>
      </ul>

      <PolicyHeading>How to start a return</PolicyHeading>
      <ol className="list-decimal space-y-2 pl-5">
        <li>
          Email{' '}
          <a href={`mailto:${siteConfig.contact.email}`} className="underline">
            {siteConfig.contact.email}
          </a>{' '}
          or use the{' '}
          <Link href="/contact" className="underline">
            contact form
          </Link>{' '}
          with your order reference.
        </li>
        <li>Tell us which items you are returning and whether you want a refund or an exchange.</li>
        <li>We will reply with the next steps.</li>
      </ol>

      <PolicyHeading>Exchanges</PolicyHeading>
      <p>
        Exchanges are subject to stock. If your size or colour is unavailable, we will let you know
        and help you choose an alternative.
      </p>

      <p className="text-muted text-xs">
        Once we receive and check your return, we will confirm the outcome by email.
      </p>
    </PolicyPage>
  );
}
