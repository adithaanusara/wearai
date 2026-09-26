'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { hasRole } from '@/lib/admin';
import type { Role } from '@/types/api';

const links: { href: string; label: string; minimum: Role }[] = [
  { href: '/admin', label: 'Dashboard', minimum: 'staff' },
  { href: '/admin/users', label: 'Users', minimum: 'admin' },
  { href: '/admin/audit-log', label: 'Audit log', minimum: 'admin' },
];

export function AdminNav({ role }: { role: Role }) {
  const pathname = usePathname();

  return (
    <nav aria-label="Admin" className="border-border border-b">
      <ul className="flex flex-wrap gap-x-6 gap-y-2 py-3 text-xs font-medium tracking-wide uppercase">
        {links
          .filter((link) => hasRole(role, link.minimum))
          .map((link) => {
            const current = pathname === link.href;
            return (
              <li key={link.href}>
                <Link
                  href={link.href}
                  aria-current={current ? 'page' : undefined}
                  className={
                    current ? 'underline underline-offset-4' : 'text-muted hover:text-text'
                  }
                >
                  {link.label}
                </Link>
              </li>
            );
          })}
      </ul>
    </nav>
  );
}
