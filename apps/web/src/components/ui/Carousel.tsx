'use client';

import { useRef, type ReactNode } from 'react';
import { ChevronIcon } from '@/components/ui/icons';

interface CarouselProps {
  label: string;
  /** List items, each one slide. */
  children: ReactNode;
}

export function Carousel({ label, children }: CarouselProps) {
  const trackRef = useRef<HTMLUListElement>(null);

  function scrollByPage(direction: 1 | -1) {
    const track = trackRef.current;
    if (!track) return;
    const reduceMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    track.scrollBy({
      left: direction * track.clientWidth * 0.8,
      behavior: reduceMotion ? 'auto' : 'smooth',
    });
  }

  const buttonClass =
    'border-border bg-bg absolute top-1/3 z-10 hidden h-10 w-10 items-center justify-center rounded-sm border md:flex';

  return (
    <div className="relative">
      <ul
        ref={trackRef}
        tabIndex={0}
        aria-label={label}
        className="-mx-(--gutter) flex snap-x snap-mandatory gap-4 overflow-x-auto px-(--gutter) pb-2 [scrollbar-width:none] md:mx-0 md:px-0 [&::-webkit-scrollbar]:hidden"
      >
        {children}
      </ul>
      <button
        type="button"
        aria-label="Previous"
        className={`${buttonClass} left-2`}
        onClick={() => scrollByPage(-1)}
      >
        <ChevronIcon className="h-5 w-5 rotate-90" />
      </button>
      <button
        type="button"
        aria-label="Next"
        className={`${buttonClass} right-2`}
        onClick={() => scrollByPage(1)}
      >
        <ChevronIcon className="h-5 w-5 -rotate-90" />
      </button>
    </div>
  );
}
