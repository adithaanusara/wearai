import { ButtonLink } from '@/components/ui/ButtonLink';

interface CheckoutButtonProps {
  enabled: boolean;
  onNavigate?: () => void;
  className?: string;
}

/** A link to checkout that is switched off while the cart cannot be ordered. */
export function CheckoutButton({ enabled, onNavigate, className = '' }: CheckoutButtonProps) {
  if (!enabled) {
    return (
      <button
        type="button"
        disabled
        className={`bg-text text-bg inline-flex items-center justify-center rounded-sm border border-text px-8 py-3 text-xs font-medium tracking-wide uppercase opacity-40 ${className}`}
      >
        Checkout
      </button>
    );
  }
  return (
    <ButtonLink href="/checkout" variant="primary" onClick={onNavigate} className={className}>
      Checkout
    </ButtonLink>
  );
}
