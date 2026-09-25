import type { Metadata } from 'next';
import { ContactForm } from '@/components/contact/ContactForm';
import { PolicyHeading, PolicyPage } from '@/components/layout/PolicyPage';
import { siteConfig } from '@/config/site';

export const metadata: Metadata = { title: 'Contact' };

export default function ContactPage() {
  const { email, phone, hours } = siteConfig.contact;

  return (
    <PolicyPage title="Contact us">
      <p>Questions about an order, sizing or a product? We are happy to help.</p>

      <dl className="space-y-3">
        <div>
          <dt className="text-muted text-xs">Email</dt>
          <dd>
            <a href={`mailto:${email}`} className="underline">
              {email}
            </a>
          </dd>
        </div>
        <div>
          <dt className="text-muted text-xs">Phone</dt>
          <dd>
            <a href={`tel:${phone.replace(/\s/g, '')}`} className="underline">
              {phone}
            </a>
          </dd>
        </div>
        <div>
          <dt className="text-muted text-xs">Hours</dt>
          <dd>{hours}</dd>
        </div>
      </dl>

      <PolicyHeading>Send us a message</PolicyHeading>
      <ContactForm />
    </PolicyPage>
  );
}
