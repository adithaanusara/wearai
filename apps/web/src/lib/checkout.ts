import { provinces } from '@/data/locations';
import { deliveryMethods, paymentMethods } from '@/data/shipping';

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

export type CheckoutErrors = Partial<Record<keyof CheckoutValues, string>>;

const emailPattern = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
// Sri Lankan mobile numbers: 07X XXX XXXX or +94 7X XXX XXXX.
const phonePattern = /^(?:\+94|0)7\d{8}$/;
const postalCodePattern = /^\d{5}$/;

export function validateCheckout(values: CheckoutValues): CheckoutErrors {
  const errors: CheckoutErrors = {};

  if (!emailPattern.test(values.email.trim())) errors.email = 'Enter a valid email address.';

  if (!phonePattern.test(values.phone.replace(/[\s-]/g, ''))) {
    errors.phone = 'Enter a valid mobile number, like 077 123 4567.';
  }

  if (!values.fullName.trim()) errors.fullName = 'Enter your full name.';
  if (!values.address1.trim()) errors.address1 = 'Enter your address.';
  if (!values.city.trim()) errors.city = 'Enter your city.';

  const province = provinces.find((candidate) => candidate.name === values.province);
  if (!province) errors.province = 'Select a province.';

  if (!province || !province.districts.includes(values.district)) {
    errors.district = 'Select a district.';
  }

  if (!postalCodePattern.test(values.postalCode.trim())) {
    errors.postalCode = 'Enter a 5-digit postal code.';
  }

  if (!deliveryMethods.some((method) => method.id === values.deliveryMethod)) {
    errors.deliveryMethod = 'Select a delivery method.';
  }
  if (!paymentMethods.some((method) => method.id === values.paymentMethod)) {
    errors.paymentMethod = 'Select a payment method.';
  }

  return errors;
}
