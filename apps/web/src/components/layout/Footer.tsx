import { Container } from '@/components/ui/Container';
import { siteConfig } from '@/config/site';

export function Footer() {
  return (
    <footer className="bg-dark text-bg">
      <Container className="py-8 text-sm">
        &copy; {new Date().getFullYear()} {siteConfig.name}
      </Container>
    </footer>
  );
}
