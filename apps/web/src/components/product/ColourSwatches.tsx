import Link from 'next/link';
import { swatchColours } from '@/data/colours';
import type { Product } from '@/types/product';

interface ColourSwatchesProps {
  current: Product;
  colourways: Product[];
}

export function ColourSwatches({ current, colourways }: ColourSwatchesProps) {
  return (
    <div>
      <p className="text-sm">
        <span className="text-muted">Colour:</span> {current.colour}
      </p>
      {colourways.length > 1 && (
        <ul className="mt-3 flex gap-3">
          {colourways.map((item) => {
            const isCurrent = item.id === current.id;
            return (
              <li key={item.id}>
                <Link
                  href={`/products/${item.slug}`}
                  aria-label={item.colour}
                  aria-current={isCurrent ? 'true' : undefined}
                  className={`block h-9 w-9 rounded-sm border-2 p-0.5 ${
                    isCurrent ? 'border-text' : 'border-border'
                  }`}
                >
                  <span
                    className="border-border block h-full w-full rounded-sm border"
                    style={{ backgroundColor: swatchColours[item.colour] }}
                  />
                </Link>
              </li>
            );
          })}
        </ul>
      )}
    </div>
  );
}
