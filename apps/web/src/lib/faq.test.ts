import { describe, expect, it } from 'vitest';
import { deliveryMethods, paymentMethods } from '@/data/shipping';
import { getFaqItems } from '@/lib/faq';
import { formatPrice } from '@/lib/format';

describe('getFaqItems', () => {
  const items = getFaqItems();
  const find = (text: string) => items.find((item) => item.question.includes(text))!;

  it('has a non-empty question and answer for every entry', () => {
    expect(items.length).toBeGreaterThan(0);
    for (const item of items) {
      expect(item.question.trim()).not.toBe('');
      expect(item.answer.trim()).not.toBe('');
    }
  });

  it('quotes every delivery fee from the shipping data', () => {
    const answer = find('delivery cost').answer;
    for (const method of deliveryMethods) {
      expect(answer).toContain(method.label);
      if (method.fee > 0) expect(answer).toContain(formatPrice(method.fee));
    }
  });

  it('names every payment method', () => {
    const answer = find('payment methods').answer;
    for (const method of paymentMethods) {
      expect(answer).toContain(method.label.toLowerCase());
    }
  });
});
