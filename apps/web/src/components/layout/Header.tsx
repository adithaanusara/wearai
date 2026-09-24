import Link from 'next/link';
import { DesktopNav } from '@/components/layout/DesktopNav';
import { MobileMenu } from '@/components/layout/MobileMenu';
import { Container } from '@/components/ui/Container';
import { BagIcon, SearchIcon, UserIcon } from '@/components/ui/icons';
import { siteConfig } from '@/config/site';
import { mainNav } from '@/data/navigation';

interface HeaderProps {
  cartCount?: number;
}

export function Header({ cartCount = 0 }: HeaderProps) {
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
          <Link href="/account" aria-label="Account" className="hidden p-2 sm:block">
            <UserIcon />
          </Link>
          <Link
            href="/cart"
            aria-label={`Cart, ${cartCount} ${cartCount === 1 ? 'item' : 'items'}`}
            className="relative -mr-2 p-2"
          >
            <BagIcon />
            {cartCount > 0 && (
              <span className="bg-text text-bg absolute top-0.5 right-0.5 flex h-4 min-w-4 items-center justify-center rounded-sm px-1 text-[10px] leading-none font-medium">
                {cartCount}
              </span>
            )}
          </Link>
        </div>
      </Container>
    </header>
  );
}
