import { siteConfig } from '@/config/site';

export default function Home() {
  return (
    <main className="flex flex-1 items-center justify-center">
      <h1 className="text-3xl font-bold uppercase tracking-wide">{siteConfig.name}</h1>
    </main>
  );
}
