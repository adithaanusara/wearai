import type { Metadata } from 'next';
import { PolicyPage } from '@/components/layout/PolicyPage';
import { ChevronIcon } from '@/components/ui/icons';
import { getFaqItems } from '@/lib/faq';

export const metadata: Metadata = { title: 'FAQ' };

export default function FaqPage() {
  return (
    <PolicyPage title="Frequently asked questions">
      <div className="divide-border border-border divide-y border-y">
        {getFaqItems().map((item) => (
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
