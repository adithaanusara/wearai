import type { Metadata } from 'next';
import { PolicyPage } from '@/components/layout/PolicyPage';
import { ChevronIcon } from '@/components/ui/icons';
import { getCheckoutOptions } from '@/lib/api';
import { getFaqItems } from '@/lib/faq';

export const metadata: Metadata = { title: 'FAQ' };

// Delivery fees come from the store API, so this page renders on request.
export const dynamic = 'force-dynamic';

export default async function FaqPage() {
  const options = await getCheckoutOptions();

  return (
    <PolicyPage title="Frequently asked questions">
      <div className="divide-border border-border divide-y border-y">
        {getFaqItems(options).map((item) => (
          <details key={item.question} className="group py-4">
            <summary className="flex cursor-pointer list-none items-center justify-between gap-4 font-medium [&::-webkit-details-marker]:hidden">
              {item.question}
              <ChevronIcon className="h-4 w-4 shrink-0 transition-transform group-open:rotate-180" />
            </summary>
            <p className="mt-3">{item.answer}</p>
          </details>
        ))}
      </div>
    </PolicyPage>
  );
}
