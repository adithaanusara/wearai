'use client';

import { useRef, useState, type KeyboardEvent } from 'react';
import { Container } from '@/components/ui/Container';
import { ImageTile } from '@/components/ui/ImageTile';
import { activities } from '@/data/home';

export function ShopByActivity() {
  const [activeId, setActiveId] = useState(activities[0].id);
  const tabRefs = useRef<(HTMLButtonElement | null)[]>([]);
  const active = activities.find((activity) => activity.id === activeId) ?? activities[0];

  function onKeyDown(event: KeyboardEvent, index: number) {
    const last = activities.length - 1;
    const next =
      event.key === 'ArrowRight'
        ? (index + 1) % activities.length
        : event.key === 'ArrowLeft'
          ? (index - 1 + activities.length) % activities.length
          : event.key === 'Home'
            ? 0
            : event.key === 'End'
              ? last
              : null;
    if (next === null) return;
    event.preventDefault();
    setActiveId(activities[next].id);
    tabRefs.current[next]?.focus();
  }

  return (
    <section aria-labelledby="activity-title" className="bg-surface py-12 md:py-16">
      <Container>
        <h2 id="activity-title" className="text-2xl font-bold tracking-wide uppercase md:text-3xl">
          Shop by activity
        </h2>

        <div role="tablist" aria-label="Shop by activity" className="mt-6 flex gap-6">
          {activities.map((activity, index) => {
            const selected = activity.id === activeId;
            return (
              <button
                key={activity.id}
                ref={(element) => {
                  tabRefs.current[index] = element;
                }}
                role="tab"
                id={`activity-tab-${activity.id}`}
                aria-selected={selected}
                aria-controls={`activity-panel-${activity.id}`}
                tabIndex={selected ? 0 : -1}
                className={`border-b-2 pb-1 text-xs font-medium tracking-wide uppercase ${
                  selected ? 'border-text' : 'text-muted border-transparent'
                }`}
                onClick={() => setActiveId(activity.id)}
                onKeyDown={(event) => onKeyDown(event, index)}
              >
                {activity.label}
              </button>
            );
          })}
        </div>

        <div
          role="tabpanel"
          id={`activity-panel-${active.id}`}
          aria-labelledby={`activity-tab-${active.id}`}
          className="mt-6"
        >
          <ul className="grid grid-cols-2 gap-4 md:grid-cols-4">
            {active.tiles.map((tile) => (
              <li key={tile.href}>
                <ImageTile {...tile} />
              </li>
            ))}
          </ul>
        </div>
      </Container>
    </section>
  );
}
