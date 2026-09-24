import { Hero } from '@/components/home/Hero';
import { LatestStyles } from '@/components/home/LatestStyles';
import { PromoBanner } from '@/components/home/PromoBanner';
import { ShopByCategory } from '@/components/home/ShopByCategory';

export default function Home() {
  return (
    <>
      <Hero />
      <LatestStyles />
      <PromoBanner />
      <ShopByCategory />
    </>
  );
}
