import Image from 'next/image';
import { ButtonLink } from '@/components/ui/ButtonLink';
import { Container } from '@/components/ui/Container';
import { promo } from '@/data/home';

export function PromoBanner() {
  return (
    <section aria-labelledby="promo-title" className="text-bg relative flex min-h-96 items-center">
      <Image src={promo.image} alt="" fill sizes="100vw" className="object-cover" />
      <div className="bg-dark/60 absolute inset-0" aria-hidden="true" />

      <Container className="relative py-16 text-center">
        <h2 id="promo-title" className="text-3xl font-bold tracking-tight uppercase md:text-5xl">
          {promo.headline}
        </h2>
        <p className="mx-auto mt-3 max-w-md text-sm md:text-base">{promo.text}</p>
        <ButtonLink href={promo.cta.href} variant="light" className="mt-8">
          {promo.cta.label}
        </ButtonLink>
      </Container>
    </section>
  );
}
