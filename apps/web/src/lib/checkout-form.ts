import type { ApiProblem } from '@/lib/api';

export interface CheckoutValues {
  email: string;
  phone: string;
  fullName: string;
  address1: string;
  address2: string;
  city: string;
  province: string;
  district: string;
  postalCode: string;
  deliveryMethod: string;
  paymentMethod: string;
}

export type CheckoutField = keyof CheckoutValues;
export type CheckoutErrors = Partial<Record<CheckoutField, string>>;

/** Order of the fields on the page, used to focus the first one with a problem. */
export const FIELD_ORDER: CheckoutField[] = [
  'email',
  'phone',
  'fullName',
  'address1',
  'address2',
  'city',
  'province',
  'district',
  'postalCode',
  'deliveryMethod',
  'paymentMethod',
];

export const initialValues: CheckoutValues = {
  email: '',
  phone: '',
  fullName: '',
  address1: '',
  address2: '',
  city: '',
  province: '',
  district: '',
  postalCode: '',
  deliveryMethod: 'standard',
  paymentMethod: 'cod',
};

export interface MappedProblems {
  /** One message per form field. */
  fields: CheckoutErrors;
  /** True when a cart line is the problem, for example a product that no longer exists. */
  cartProblem: boolean;
  /** A message for anything that belongs to no field. */
  other: string | null;
}

/** Sorts the API's problems into form fields, the cart, and everything else. */
export function mapProblems(problems: ApiProblem[]): MappedProblems {
  const fields: CheckoutErrors = {};
  let cartProblem = false;
  let other: string | null = null;

  for (const { loc, msg } of problems) {
    if (loc.includes('items')) {
      cartProblem = true;
      continue;
    }
    const name = loc[loc.length - 1];
    if (typeof name === 'string' && FIELD_ORDER.includes(name as CheckoutField)) {
      // The first message for a field is the most useful one.
      fields[name as CheckoutField] ??= msg;
    } else {
      other ??= msg;
    }
  }
  return { fields, cartProblem, other };
}

export function firstInvalidField(errors: CheckoutErrors): CheckoutField | undefined {
  return FIELD_ORDER.find((field) => errors[field]);
}
