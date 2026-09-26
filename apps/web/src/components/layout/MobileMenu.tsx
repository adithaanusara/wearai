'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { useEffect, useRef, useState } from 'react';
import { useSession } from '@/components/account/useSession';
import { ChevronIcon, CloseIcon, MenuIcon } from '@/components/ui/icons';
import type { NavItem, NavLink } from '@/data/navigation';

export function MobileMenu({ items }: { items: NavItem[] }) {
  const pathname = usePathname();
  const { session } = useSession();
  // Storing the path the menu was opened on closes it automatically on navigation.
  const [openedAt, setOpenedAt] = useState<string | null>(null);
  const open = openedAt === pathname;
  const buttonRef = useRef<HTMLButtonElement>(null);

  function close() {
    setOpenedAt(null);
    buttonRef.current?.focus();
  }

  useEffect(() => {
    if (!open) return;
    const previousOverflow = document.body.style.overflow;
    document.body.style.overflow = 'hidden';

    function onKeyDown(event: KeyboardEvent) {
      if (event.key === 'Escape') {
        setOpenedAt(null);
        buttonRef.current?.focus();
      }
    }
    document.addEventListener('keydown', onKeyDown);

    // The menu is hidden from the lg breakpoint up, so it must not keep the page locked there.
    const desktop = window.matchMedia('(min-width: 1024px)');
    function onBreakpointChange(event: MediaQueryListEvent) {
      if (event.matches) setOpenedAt(null);
    }
    desktop.addEventListener('change', onBreakpointChange);

    return () => {
      document.body.style.overflow = previousOverflow;
      document.removeEventListener('keydown', onKeyDown);
      desktop.removeEventListener('change', onBreakpointChange);
    };
  }, [open]);

  return (
    <div className="lg:hidden">
      <button
        ref={buttonRef}
        type="button"
        className="-ml-2 p-2"
        aria-label={open ? 'Close menu' : 'Open menu'}
        aria-expanded={open}
        aria-controls="mobile-menu"
        onClick={() => (open ? close() : setOpenedAt(pathname))}
      >
        {open ? <CloseIcon /> : <MenuIcon />}
      </button>

      {open && (
        <nav
          id="mobile-menu"
          aria-label="Main"
          className="bg-bg fixed inset-x-0 top-(--header-height) bottom-0 overflow-y-auto"
        >
          <ul className="divide-border divide-y px-(--gutter)">
            {items.map((item) => (
              <MobileNavItem key={item.href} item={item} />
            ))}
            <li>
              <Link href={session ? '/account' : '/login'} className={`${rowClass} block`}>
                {session ? 'My account' : 'Sign in'}
              </Link>
            </li>
          </ul>
        </nav>
      )}
    </div>
  );
}

const rowClass = 'py-5 text-sm font-medium tracking-wide uppercase';

function MobileNavItem({ item }: { item: NavItem }) {
  const [expanded, setExpanded] = useState(false);
  const panelId = `mobile-${item.label.toLowerCase().replace(/\s+/g, '-')}`;

  if (!item.menu) {
    return (
      <li>
        <Link href={item.href} className={`${rowClass} block`}>
          {item.label}
        </Link>
      </li>
    );
  }

  return (
    <li>
      <button
        type="button"
        className={`${rowClass} flex w-full items-center justify-between`}
        aria-expanded={expanded}
        aria-controls={expanded ? panelId : undefined}
        onClick={() => setExpanded(!expanded)}
      >
        {item.label}
        <ChevronIcon className={`h-4 w-4 transition-transform ${expanded ? 'rotate-180' : ''}`} />
      </button>
      {expanded && (
        <div id={panelId} className="space-y-6 pb-6">
          <MobileLinks title="Featured" links={item.menu.featured} />
          <MobileLinks title={`Explore ${item.label}`} links={item.menu.explore} />
        </div>
      )}
    </li>
  );
}

function MobileLinks({ title, links }: { title: string; links: NavLink[] }) {
  return (
    <div>
      <h2 className="text-muted mb-3 text-xs font-medium tracking-wide uppercase">{title}</h2>
      <ul className="space-y-3">
        {links.map((link) => (
          <li key={link.href}>
            <Link href={link.href} className="text-sm">
              {link.label}
            </Link>
          </li>
        ))}
      </ul>
    </div>
  );
}
