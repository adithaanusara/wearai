'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { useEffect, useRef, useState } from 'react';
import { CloseIcon, MenuIcon } from '@/components/ui/icons';
import type { NavItem } from '@/data/navigation';

export function MobileMenu({ items }: { items: NavItem[] }) {
  const pathname = usePathname();
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
          className="bg-bg fixed inset-x-0 top-16 bottom-0 overflow-y-auto"
        >
          <ul className="divide-border divide-y px-(--gutter)">
            {items.map((item) => (
              <li key={item.href}>
                <Link
                  href={item.href}
                  className="block py-5 text-sm font-medium tracking-wide uppercase"
                >
                  {item.label}
                </Link>
              </li>
            ))}
          </ul>
        </nav>
      )}
    </div>
  );
}
