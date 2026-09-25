export type Gender = 'women' | 'men' | 'unisex';

export type Category =
  | 't-shirts'
  | 'leggings'
  | 'hoodies'
  | 'shorts'
  | 'joggers'
  | 'bags'
  | 'caps'
  | 'socks'
  | 'bottles';

export interface Product {
  id: string;
  slug: string;
  /** Products with the same styleId are the same item in different colours. */
  styleId: string;
  name: string;
  gender: Gender;
  category: Category;
  colour: string;
  /** Price in whole LKR. */
  price: number;
  /** Original price in whole LKR, set when the product is on sale. */
  compareAtPrice?: number | null;
  /** The first image is the default; the second, when there is one, is shown on hover. */
  images: string[];
  sizes: string[];
  isNew: boolean;
  isBestSeller?: boolean;
  description: string;
  details: string[];
}
