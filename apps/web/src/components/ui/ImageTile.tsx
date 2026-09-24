import Image from 'next/image';
import Link from 'next/link';

interface ImageTileProps {
  title: string;
  href: string;
  image: string;
  imageSizes?: string;
}

export function ImageTile({
  title,
  href,
  image,
  imageSizes = '(min-width: 768px) 25vw, 50vw',
}: ImageTileProps) {
  return (
    <Link href={href} className="group block">
      <div className="bg-surface relative aspect-4/5 overflow-hidden">
        <Image
          src={image}
          alt=""
          fill
          sizes={imageSizes}
          className="object-cover transition-transform duration-300 group-hover:scale-105"
        />
      </div>
      <span className="mt-3 block text-xs font-medium tracking-wide uppercase group-hover:underline">
        {title}
      </span>
    </Link>
  );
}
