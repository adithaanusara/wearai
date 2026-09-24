import { Container } from '@/components/ui/Container';
import { siteConfig } from '@/config/site';

export function Header() {
  return (
    <header className="border-border border-b">
      <Container className="flex h-16 items-center">
        <span className="text-lg font-bold tracking-wide uppercase">{siteConfig.name}</span>
      </Container>
    </header>
  );
}
