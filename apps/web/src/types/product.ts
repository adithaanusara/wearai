export type Gender = 'women' | 'men' | 'unisex';

export type Category = 't-shirts' | 'leggings' | 'hoodies' | 'shorts' | 'joggers' | 'bags' | 'caps';

export interface Product {
  id: string;
  slug: string;
  name: string;
  gender: Gender;
  category: Category;
  colour: string;
  /** Price in whole LKR. */
  price: number;
  /** First image is the default; the second is shown on hover. */
  images: [string, string];
  sizes: string[];
  isNew: boolean;
}
