interface StarsProps {
  rating: number;
  className?: string;
}

/** Five-star rating shown as text glyphs, with the value available to screen readers. */
export function Stars({ rating, className = '' }: StarsProps) {
  const filled = Math.round(rating);
  return (
    <span
      role="img"
      aria-label={`${rating} out of 5 stars`}
      className={`tracking-wider ${className}`}
    >
      <span aria-hidden="true">
        {[1, 2, 3, 4, 5].map((star) => (
          <span key={star} className={star <= filled ? 'text-text' : 'text-border'}>
            ★
          </span>
        ))}
      </span>
    </span>
  );
}
