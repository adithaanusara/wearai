import { describe, expect, it } from 'vitest';
import { products } from '@/data/products';
import { getMockReply } from '@/lib/chat-mock';

const byId = (id: string) => products.find((product) => product.id === id)!;

describe('getMockReply', () => {
  it('recommends products for a category and returns real product ids', () => {
    const reply = getMockReply('Can you find me a hoodie?');
    expect(reply.productIds?.length).toBeGreaterThan(0);
    expect(reply.productIds?.every((id) => byId(id).category === 'hoodies')).toBe(true);
  });

  it('respects a gender in the request', () => {
    const reply = getMockReply("show me women's leggings");
    expect(reply.productIds?.length).toBeGreaterThan(0);
    expect(reply.productIds?.every((id) => byId(id).gender !== 'men')).toBe(true);
  });

  it('suggests at most three products, one per style', () => {
    const reply = getMockReply('any t-shirts?');
    expect(reply.productIds!.length).toBeLessThanOrEqual(3);
    const styles = reply.productIds!.map((id) => byId(id).styleId);
    expect(new Set(styles).size).toBe(styles.length);
  });

  it('finds sale items', () => {
    const reply = getMockReply('anything on sale?');
    expect(reply.productIds?.every((id) => byId(id).compareAtPrice !== undefined)).toBe(true);
  });

  it('answers delivery questions from the shipping data', () => {
    const reply = getMockReply('How much is delivery?');
    expect(reply.text).toContain('LKR 450.00');
    expect(reply.productIds).toBeUndefined();
  });

  it('answers payment, size and returns questions', () => {
    expect(getMockReply('can I pay cash?').text).toMatch(/cash on delivery/);
    expect(getMockReply('what size should I get').text).toMatch(/size guide/);
    expect(getMockReply('I want a refund').text).toMatch(/Returns & Exchanges/);
  });

  it('prefers policy answers over product matches', () => {
    expect(getMockReply('can I return a hoodie?').productIds).toBeUndefined();
  });

  it('greets and falls back politely', () => {
    expect(getMockReply('hello').text).toMatch(/Hello/);
    expect(getMockReply('what is the meaning of life').text).toMatch(/not sure/);
  });
});
