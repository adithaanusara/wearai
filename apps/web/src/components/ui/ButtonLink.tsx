import Link from 'next/link';
import type { ComponentPropsWithoutRef } from 'react';

type Variant = 'primary' | 'secondary' | 'light' | 'outline-light';

const variants: Record<Variant, string> = {
  primary: 'bg-text text-bg border-text hover:bg-dark-2',
  secondary: 'bg-bg text-text border-text hover:bg-surface',
  light: 'bg-bg text-text border-bg hover:bg-surface',
  'outline-light': 'bg-transparent text-bg border-bg hover:bg-bg hover:text-text',
};

interface ButtonLinkProps extends ComponentPropsWithoutRef<typeof Link> {
  variant?: Variant;
}

export function ButtonLink({ variant = 'primary', className = '', ...props }: ButtonLinkProps) {
  return (
    <Link
      className={`inline-flex items-center justify-center rounded-sm border px-8 py-3 text-xs font-medium tracking-wide uppercase transition-colors ${variants[variant]} ${className}`}
      {...props}
    />
  );
}
