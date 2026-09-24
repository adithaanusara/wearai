'use client';

import Image from 'next/image';
import { useState } from 'react';

interface ProductGalleryProps {
  images: string[];
  /** Describes the product, e.g. "Pullover Hoodie in Black". */
  alt: string;
}

export function ProductGallery({ images, alt }: ProductGalleryProps) {
  const [selected, setSelected] = useState(0);

  return (
    <div className="space-y-3">
      <div className="bg-surface relative aspect-4/5">
        <Image
          src={images[selected]}
          alt={`${alt}, image ${selected + 1} of ${images.length}`}
          fill
          priority
          sizes="(min-width: 1024px) 50vw, 100vw"
          className="object-cover"
        />
      </div>

      {images.length > 1 && (
        <ul className="grid grid-cols-5 gap-3">
          {images.map((image, index) => (
            <li key={image + index}>
              <button
                type="button"
                aria-label={`Show image ${index + 1}`}
                aria-pressed={index === selected}
                className={`bg-surface relative block aspect-4/5 w-full border-2 ${
                  index === selected ? 'border-text' : 'border-transparent'
                }`}
                onClick={() => setSelected(index)}
              >
                <Image src={image} alt="" fill sizes="10vw" className="object-cover" />
              </button>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
