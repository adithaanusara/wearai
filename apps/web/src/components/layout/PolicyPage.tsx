import type { ReactNode } from 'react';
import { Container } from '@/components/ui/Container';

interface PolicyPageProps {
  title: string;
  children: ReactNode;
}

/** A narrow, readable column for text pages such as policies. */
export function PolicyPage({ title, children }: PolicyPageProps) {
  return (
    <Container className="py-10 md:py-14">
      <div className="max-w-2xl">
        <h1 className="text-3xl font-bold tracking-wide uppercase md:text-4xl">{title}</h1>
        <div className="mt-8 space-y-6 text-sm leading-relaxed">{children}</div>
      </div>
    </Container>
  );
}

export function PolicyHeading({ children }: { children: ReactNode }) {
  return <h2 className="pt-4 text-lg font-bold tracking-wide uppercase">{children}</h2>;
}
