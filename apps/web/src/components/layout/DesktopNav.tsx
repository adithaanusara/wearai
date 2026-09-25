'use client';

import Image from 'next/image';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { useEffect, useRef, useState } from 'react';
import type { FocusEvent } from 'react';
import { Container } from '@/components/ui/Container';
import type { NavItem, NavMenu } from '@/data/navigation';

const HOVER_CLOSE_DELAY_MS = 150;

const linkClass = 'text-xs font-medium tracking-wide uppercase';

export function DesktopNav({ items }: { items: NavItem[] }) {
  const pathname = usePathname();
  // The menu is tied to the path it was opened on, so it closes on navigation.
  const [open, setOpen] = useState<{ label: string; path: string } | null>(null);
  const activeLabel = open?.path === pathname ? open.label : null;
  const navRef = useRef<HTMLElement>(null);
  const closeTimer = useRef<number | undefined>(undefined);

  function openMenu(label: string) {
    window.clearTimeout(closeTimer.current);
    setOpen({ label, path: pathname });
  }

  function closeMenu() {
    window.clearTimeout(closeTimer.current);
    setOpen(null);
  }

  function closeMenuSoon() {
    window.clearTimeout(closeTimer.current);
    closeTimer.current = window.setTimeout(() => setOpen(null), HOVER_CLOSE_DELAY_MS);
  }

  function onBlur(event: FocusEvent<HTMLLIElement>) {
    if (!event.currentTarget.contains(event.relatedTarget)) closeMenu();
  }

  useEffect(() => {
    if (!activeLabel) return;
    function onPointerDown(event: PointerEvent) {
      if (!navRef.current?.contains(event.target as Node)) setOpen(null);
    }
    // Escape must dismiss the menu however it was opened, including by hover with no focus inside it.
    function onKeyDown(event: KeyboardEvent) {
      if (event.key !== 'Escape') return;
      const nav = navRef.current;
      const trigger = nav?.querySelector<HTMLElement>('button[aria-expanded="true"]');
      const focusWasInside = nav?.contains(document.activeElement);
      setOpen(null);
      if (focusWasInside) trigger?.focus();
    }
    document.addEventListener('pointerdown', onPointerDown);
    document.addEventListener('keydown', onKeyDown);
    return () => {
      document.removeEventListener('pointerdown', onPointerDown);
      document.removeEventListener('keydown', onKeyDown);
    };
  }, [activeLabel]);

  useEffect(() => () => window.clearTimeout(closeTimer.current), []);

  return (
    <nav ref={navRef} aria-label="Main" className="hidden lg:block">
      <ul className="flex gap-8">
        {items.map((item) => {
          const expanded = activeLabel === item.label;
          const panelId = `mega-${item.label.toLowerCase().replace(/\s+/g, '-')}`;

          if (!item.menu) {
            return (
              <li key={item.href} onPointerEnter={closeMenuSoon}>
                <Link
                  href={item.href}
                  className={`${linkClass} flex h-(--header-height) items-center hover:underline`}
                >
                  {item.label}
                </Link>
              </li>
            );
          }

          return (
            <li
              key={item.href}
              onPointerEnter={(event) => event.pointerType === 'mouse' && openMenu(item.label)}
              onPointerLeave={(event) => event.pointerType === 'mouse' && closeMenuSoon()}
              onBlur={onBlur}
            >
              <button
                type="button"
                aria-expanded={expanded}
                aria-controls={expanded ? panelId : undefined}
                className={`${linkClass} flex h-(--header-height) items-center hover:underline ${
                  expanded ? 'underline' : ''
                }`}
                onClick={() => openMenu(item.label)}
              >
                {item.label}
              </button>
              {expanded && (
                <MegaPanel
                  id={panelId}
                  label={item.label}
                  menu={item.menu}
                  onNavigate={closeMenu}
                />
              )}
            </li>
          );
        })}
      </ul>
    </nav>
  );
}

interface MegaPanelProps {
  id: string;
  label: string;
  menu: NavMenu;
  onNavigate: () => void;
}

function MegaPanel({ id, label, menu, onNavigate }: MegaPanelProps) {
  return (
    <div id={id} className="border-border bg-bg absolute inset-x-0 top-full border-b">
      <Container className="grid grid-cols-[12rem_12rem_1fr] gap-12 py-10">
        <MegaLinks title="Featured" links={menu.featured} onNavigate={onNavigate} />
        <MegaLinks title={`Explore ${label}`} links={menu.explore} onNavigate={onNavigate} />
        <ul className="grid grid-cols-3 gap-4">
          {menu.tiles.map((tile) => (
            <li key={tile.title}>
              <Link href={tile.href} onClick={onNavigate} className="group block">
                <div className="bg-surface relative aspect-4/5 overflow-hidden">
                  <Image src={tile.image} alt="" fill sizes="20vw" className="object-cover" />
                </div>
                <span className="mt-2 block text-xs font-medium tracking-wide uppercase group-hover:underline">
                  {tile.title}
                </span>
              </Link>
            </li>
          ))}
        </ul>
      </Container>
    </div>
  );
}

interface MegaLinksProps {
  title: string;
  links: { label: string; href: string }[];
  onNavigate: () => void;
}

function MegaLinks({ title, links, onNavigate }: MegaLinksProps) {
  return (
    <div>
      <h2 className="text-muted mb-4 text-xs font-medium tracking-wide uppercase">{title}</h2>
      <ul className="space-y-3">
        {links.map((link) => (
          <li key={link.href}>
            <Link href={link.href} onClick={onNavigate} className="text-sm hover:underline">
              {link.label}
            </Link>
          </li>
        ))}
      </ul>
    </div>
  );
}
