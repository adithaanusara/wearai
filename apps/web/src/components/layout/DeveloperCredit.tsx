import { siteConfig } from '@/config/site';

export function DeveloperCredit() {
  const { name, url } = siteConfig.developer;
  return (
    <p>
      Developed by{' '}
      <a
        href={url}
        target="_blank"
        rel="noopener noreferrer"
        className="font-medium underline-offset-2 hover:underline"
      >
        {name}
      </a>
    </p>
  );
}
