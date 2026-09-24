import Image from 'next/image';
import { Container } from '@/components/ui/Container';
import { ButtonLink } from '@/components/ui/ButtonLink';
import { hero } from '@/data/home';

export function Hero() {
  return (
    <section className="text-bg relative flex min-h-[70vh] items-end lg:min-h-[80vh]">
      <Image src={hero.image} alt="" fill priority sizes="100vw" className="object-cover" />
      <div className="bg-dark/50 absolute inset-0" aria-hidden="true" />

      <Container className="relative py-12 md:py-20">
        <h1 className="max-w-3xl text-4xl leading-none font-bold tracking-tight uppercase md:text-6xl">
          {hero.headline}
        </h1>
        <p className="mt-4 max-w-xl text-sm md:text-base">{hero.subtitle}</p>
        <div className="mt-8 flex flex-wrap gap-3">
          <ButtonLink href="/collections/men" variant="light">
            Shop Men
          </ButtonLink>
          <ButtonLink href="/collections/women" variant="outline-light">
            Shop Women
          </ButtonLink>
        </div>
      </Container>
    </section>
  );
}
