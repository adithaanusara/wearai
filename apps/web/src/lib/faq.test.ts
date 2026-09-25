import { describe, expect, it } from 'vitest';
import { getFaqItems } from '@/lib/faq';
import { formatPrice } from '@/lib/format';
import type { CheckoutOptions } from '@/types/api';

const options: CheckoutOptions = {
  deliveryMethods: [
    {
      id: 'standard',
      label: 'Standard delivery',
      estimate: '3–5 business days',
      fee: 450,
      freeOver: 15000,
    },
    {
      id: 'express',
      label: 'Express delivery',
      estimate: '1–2 business days',
      fee: 950,
      freeOver: null,
    },
    {
      id: 'pickup',
      label: 'Store pickup',
      estimate: 'Ready in 1 business day',
      fee: 0,
      freeOver: null,
    },
  ],
  paymentMethods: [
    { id: 'cod', label: 'Cash on delivery', note: '' },
    { id: 'card', label: 'Credit or debit card', note: '' },
  ],
  provinces: [],
};

describe('getFaqItems', () => {
  const items = getFaqItems(options);
  const find = (text: string) => items.find((item) => item.question.includes(text))!;

  it('has a non-empty question and answer for every entry', () => {
    expect(items.length).toBeGreaterThan(0);
    for (const item of items) {
      expect(item.question.trim()).not.toBe('');
      expect(item.answer.trim()).not.toBe('');
    }
  });

  it('quotes every delivery fee from the options', () => {
    const answer = find('delivery cost').answer;
    for (const method of options.deliveryMethods) {
      expect(answer).toContain(method.label);
      if (method.fee > 0) expect(answer).toContain(formatPrice(method.fee));
    }
  });

  it('mentions the free-delivery threshold only where there is one', () => {
    const answer = find('delivery cost').answer;

    expect(answer.match(/free over/g)).toHaveLength(1);
    expect(answer).toContain('free over LKR 15,000.00');
  });

  it('says a free method is free', () => {
    expect(find('delivery cost').answer).toContain('Store pickup is free');
  });

  it('names every payment method', () => {
    const answer = find('payment methods').answer;
    for (const method of options.paymentMethods) {
      expect(answer).toContain(method.label.toLowerCase());
    }
  });

  it('follows the options it is given, not fixed data', () => {
    const changed = getFaqItems({
      ...options,
      deliveryMethods: [{ ...options.deliveryMethods[0], fee: 600 }],
    });

    expect(changed[0].answer).toContain('LKR 600.00');
    expect(changed[0].answer).not.toContain('LKR 450.00');
  });
});
