import { describe, expect, it } from 'vitest';
import { validateCheckout, type CheckoutValues } from '@/lib/checkout';

const valid: CheckoutValues = {
  email: 'nimali@example.com',
  phone: '077 123 4567',
  fullName: 'Nimali Perera',
  address1: '12 Temple Road',
  address2: '',
  city: 'Nugegoda',
  province: 'Western',
  district: 'Colombo',
  postalCode: '10250',
  deliveryMethod: 'standard',
  paymentMethod: 'cod',
};

describe('validateCheckout', () => {
  it('accepts a complete, valid form', () => {
    expect(validateCheckout(valid)).toEqual({});
  });

  it('does not require the second address line', () => {
    expect(validateCheckout({ ...valid, address2: '' })).toEqual({});
  });

  it('rejects a bad email', () => {
    expect(validateCheckout({ ...valid, email: 'nimali@' }).email).toBeDefined();
  });

  it.each(['0771234567', '077-123-4567', '+94771234567', '+94 77 123 4567'])(
    'accepts the phone number %s',
    (phone) => {
      expect(validateCheckout({ ...valid, phone }).phone).toBeUndefined();
    },
  );

  it.each(['12345', '0112345678', '077123456', '+9477123456789'])(
    'rejects the phone number %s',
    (phone) => {
      expect(validateCheckout({ ...valid, phone }).phone).toBeDefined();
    },
  );

  it('requires the main address fields', () => {
    const errors = validateCheckout({ ...valid, fullName: ' ', address1: '', city: '' });
    expect(Object.keys(errors).sort()).toEqual(['address1', 'city', 'fullName']);
  });

  it('requires a district that belongs to the chosen province', () => {
    expect(validateCheckout({ ...valid, district: 'Kandy' }).district).toBeDefined();
    expect(validateCheckout({ ...valid, province: '', district: '' })).toMatchObject({
      province: expect.any(String),
      district: expect.any(String),
    });
  });

  it('requires a 5-digit postal code', () => {
    expect(validateCheckout({ ...valid, postalCode: '1025' }).postalCode).toBeDefined();
    expect(validateCheckout({ ...valid, postalCode: '1025A' }).postalCode).toBeDefined();
  });

  it('requires known delivery and payment methods', () => {
    const errors = validateCheckout({ ...valid, deliveryMethod: 'drone', paymentMethod: '' });
    expect(errors.deliveryMethod).toBeDefined();
    expect(errors.paymentMethod).toBeDefined();
  });
});
