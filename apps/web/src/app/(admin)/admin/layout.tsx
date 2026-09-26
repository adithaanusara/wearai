import type { Metadata } from 'next';
import Link from 'next/link';
import type { ReactNode } from 'react';
import { AdminNav } from '@/components/admin/AdminNav';
import { Container } from '@/components/ui/Container';
import { siteConfig } from '@/config/site';
import { roleLabel } from '@/lib/admin';
import { requireRole } from '@/lib/server-session';

export const metadata: Metadata = {
  title: { default: 'Admin', template: `%s | Admin | ${siteConfig.name}` },
  robots: { index: false, follow: false },
};

// Who is asking decides what is shown, so nothing here is prepared in advance.
export const dynamic = 'force-dynamic';

export default async function AdminLayout({ children }: { children: ReactNode }) {
  const user = await requireRole('staff');

  return (
    <>
      <header className="border-border border-b">
        <Container className="flex h-(--header-height) items-center justify-between gap-4">
          <span className="text-lg font-bold tracking-wide uppercase">{siteConfig.name} Admin</span>
          <div className="flex items-center gap-4 text-xs">
            <span className="text-muted hidden sm:inline">
              {user.email} ({roleLabel(user.role)})
            </span>
            <Link href="/" className="font-medium tracking-wide uppercase underline">
              Back to store
            </Link>
          </div>
        </Container>
      </header>
      <Container>
        <AdminNav role={user.role} />
      </Container>
      <main id="main" className="flex flex-1 flex-col">
        <Container className="py-8 md:py-10">{children}</Container>
      </main>
    </>
  );
}
