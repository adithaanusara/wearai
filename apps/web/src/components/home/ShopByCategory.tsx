import Link from 'next/link';
import { Container } from '@/components/ui/Container';
import { ImageTile } from '@/components/ui/ImageTile';
import { categoryBlocks } from '@/data/home';

export function ShopByCategory() {
  return (
    <section aria-labelledby="category-title" className="py-12 md:py-16">
      <Container className="space-y-12">
        <h2 id="category-title" className="text-2xl font-bold tracking-wide uppercase md:text-3xl">
          Shop by category
        </h2>

        {categoryBlocks.map((block) => (
          <div key={block.title}>
            <div className="mb-4 flex items-end justify-between gap-4">
              <h3 className="text-lg font-bold tracking-wide uppercase">{block.title}</h3>
              <Link
                href={block.href}
                className="text-xs font-medium tracking-wide uppercase underline"
              >
                Shop all {block.title}
              </Link>
            </div>
            <ul className="grid grid-cols-2 gap-4 md:grid-cols-4">
              {block.tiles.map((tile) => (
                <li key={tile.href}>
                  <ImageTile {...tile} />
                </li>
              ))}
            </ul>
          </div>
        ))}
      </Container>
    </section>
  );
}
