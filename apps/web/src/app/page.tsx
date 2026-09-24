import { Hero } from '@/components/home/Hero';
import { LatestStyles } from '@/components/home/LatestStyles';
import { PromoBanner } from '@/components/home/PromoBanner';

export default function Home() {
  return (
    <>
      <Hero />
      <LatestStyles />
      <PromoBanner />
    </>
  );
}
