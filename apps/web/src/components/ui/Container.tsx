import type { ComponentPropsWithoutRef } from 'react';

export function Container({ className = '', ...props }: ComponentPropsWithoutRef<'div'>) {
  return (
    <div
      className={`mx-auto w-full max-w-(--container-max) px-(--gutter) md:px-(--gutter-md) ${className}`}
      {...props}
    />
  );
}
