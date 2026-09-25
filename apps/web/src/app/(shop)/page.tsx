import { AccessoriesGrid } from '@/components/home/AccessoriesGrid';
import { Hero } from '@/components/home/Hero';
import { LatestStyles } from '@/components/home/LatestStyles';
import { PromoBanner } from '@/components/home/PromoBanner';
import { ShopByActivity } from '@/components/home/ShopByActivity';
import { ShopByCategory } from '@/components/home/ShopByCategory';
import { getCollection } from '@/lib/api';

// Shows live store data, so it renders on each request and the build does not need the API.
export const dynamic = 'force-dynamic';

export default async function Home() {
  const [latest, accessories] = await Promise.all([
    getCollection('new', { pageSize: 12 }),
    getCollection('accessories', { pageSize: 8 }),
  ]);

  return (
    <>
      <Hero />
      <LatestStyles products={latest.items} />
      <PromoBanner />
      <ShopByCategory />
      <ShopByActivity />
      <AccessoriesGrid products={accessories.items} />
    </>
  );
}
