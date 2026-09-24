import Link from 'next/link';
import { AccountLink } from '@/components/account/AccountLink';
import { CartButton } from '@/components/cart/CartButton';
import { DesktopNav } from '@/components/layout/DesktopNav';
import { MobileMenu } from '@/components/layout/MobileMenu';
import { Container } from '@/components/ui/Container';
import { SearchIcon } from '@/components/ui/icons';
import { siteConfig } from '@/config/site';
import { mainNav } from '@/data/navigation';

export function Header() {
  return (
    <header className="border-border bg-bg sticky top-0 z-40 border-b">
      <Container className="grid h-(--header-height) grid-cols-[1fr_auto_1fr] items-center">
        <div className="flex items-center">
          <MobileMenu items={mainNav} />
          <DesktopNav items={mainNav} />
        </div>

        <Link href="/" className="text-lg font-bold tracking-wide uppercase">
          {siteConfig.name}
        </Link>

        <div className="flex items-center justify-end gap-1">
          <Link href="/search" aria-label="Search" className="p-2">
            <SearchIcon />
          </Link>
          <AccountLink className="hidden sm:block" />
          <CartButton />
        </div>
      </Container>
    </header>
  );
}
