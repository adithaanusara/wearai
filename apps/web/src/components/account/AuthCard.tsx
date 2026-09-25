import type { ReactNode } from 'react';
import { Container } from '@/components/ui/Container';

interface AuthCardProps {
  title: string;
  children: ReactNode;
}

export function AuthCard({ title, children }: AuthCardProps) {
  return (
    <Container className="py-12 md:py-20">
      <div className="mx-auto max-w-md">
        <h1 className="text-3xl font-bold tracking-wide uppercase">{title}</h1>
        <div className="mt-8">{children}</div>
        <p className="text-muted mt-8 text-xs">
          Demo only: sign-in is simulated in this browser until the store backend is connected.
        </p>
      </div>
    </Container>
  );
}
