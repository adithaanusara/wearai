import Link from 'next/link';
import { Container } from '@/components/ui/Container';
import { FacebookIcon, InstagramIcon, TikTokIcon, YouTubeIcon } from '@/components/ui/icons';
import { siteConfig } from '@/config/site';
import { footerColumns, socialLinks, type SocialLink } from '@/data/footer';

const socialIcons: Record<SocialLink['platform'], typeof InstagramIcon> = {
  instagram: InstagramIcon,
  facebook: FacebookIcon,
  tiktok: TikTokIcon,
  youtube: YouTubeIcon,
};

export function Footer() {
  return (
    <footer className="bg-dark text-bg">
      <Container className="grid gap-10 py-12 md:grid-cols-3 md:py-16">
        {footerColumns.map((column) => (
          <nav key={column.title} aria-label={column.title}>
            <h2 className="mb-4 text-xs font-medium tracking-wide uppercase">{column.title}</h2>
            <ul className="space-y-3">
              {column.links.map((link) => (
                <li key={link.href}>
                  <Link
                    href={link.href}
                    className="text-sm opacity-80 hover:underline hover:opacity-100"
                  >
                    {link.label}
                  </Link>
                </li>
              ))}
            </ul>
          </nav>
        ))}

        <div>
          <h2 className="mb-4 text-xs font-medium tracking-wide uppercase">Follow us</h2>
          <ul className="flex gap-2">
            {socialLinks.map((link) => {
              const SocialIcon = socialIcons[link.platform];
              return (
                <li key={link.platform}>
                  <a
                    href={link.href}
                    target="_blank"
                    rel="noopener noreferrer"
                    aria-label={link.label}
                    className="-ml-2 block p-2 opacity-80 hover:opacity-100"
                  >
                    <SocialIcon />
                  </a>
                </li>
              );
            })}
          </ul>
        </div>
      </Container>

      <div className="border-dark-2 border-t">
        <Container className="py-6 text-xs opacity-80">
          &copy; {new Date().getFullYear()} {siteConfig.name}. All rights reserved.
        </Container>
      </div>
    </footer>
  );
}
