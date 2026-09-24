import { Container } from '@/components/ui/Container';
import { siteConfig } from '@/config/site';

export default function Home() {
  return (
    <Container className="flex flex-1 flex-col items-center justify-center gap-4 py-24">
      <h1 className="text-4xl font-bold tracking-wide uppercase">{siteConfig.name}</h1>
      <p className="text-muted">{siteConfig.description}</p>
      <a
        href="#main"
        className="bg-text text-bg rounded-sm px-6 py-3 text-sm font-medium tracking-wide uppercase"
      >
        Shop now
      </a>
    </Container>
  );
}
