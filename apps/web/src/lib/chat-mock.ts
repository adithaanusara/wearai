import { deliveryMethods, paymentMethods } from '@/data/shipping';
import { products } from '@/data/products';
import { formatPrice } from '@/lib/format';
import type { Category, Product } from '@/types/product';
import type { ChatReply } from '@/types/chat';

const MAX_SUGGESTIONS = 3;

// Placeholder logic for the UI phase. The real assistant replaces it behind sendMessage.
const categoryKeywords: [RegExp, Category][] = [
  [/\bhood(?:ie|ies)\b/, 'hoodies'],
  [/\bleggings?\b/, 'leggings'],
  [/\b(?:t-?shirts?|tees?|shirts?)\b/, 't-shirts'],
  [/\bshorts\b/, 'shorts'],
  [/\bjoggers?\b/, 'joggers'],
  [/\b(?:bags?|duffel)\b/, 'bags'],
  [/\bcaps?\b/, 'caps'],
  [/\bsocks?\b/, 'socks'],
  [/\b(?:bottles?)\b/, 'bottles'],
];

function pickProducts(text: string): Product[] {
  const category = categoryKeywords.find(([pattern]) => pattern.test(text))?.[1];
  const wantsWomen = /\bwom[ae]n'?s?\b|\bladies\b/.test(text);
  const wantsMen = /\bmen'?s?\b/.test(text) && !wantsWomen;

  let matches = products;
  if (category) matches = matches.filter((product) => product.category === category);
  else if (/\b(?:new|latest)\b/.test(text)) matches = matches.filter((product) => product.isNew);
  else if (/\b(?:sale|discount|offers?|cheap)\b/.test(text)) {
    matches = matches.filter((product) => product.compareAtPrice !== undefined);
  } else if (/\bbest[- ]?sellers?\b|\bpopular\b/.test(text)) {
    matches = matches.filter((product) => product.isBestSeller);
  } else return [];

  if (wantsWomen) matches = matches.filter((product) => product.gender !== 'men');
  if (wantsMen) matches = matches.filter((product) => product.gender !== 'women');

  // One suggestion per style, so a product does not appear twice in different colours.
  const seen = new Set<string>();
  return matches
    .filter((product) => !seen.has(product.styleId) && seen.add(product.styleId))
    .slice(0, MAX_SUGGESTIONS);
}

function shippingAnswer(): string {
  const lines = deliveryMethods.map((method) => {
    const fee = method.fee === 0 ? 'free' : formatPrice(method.fee);
    const free = method.freeOver ? `, free over ${formatPrice(method.freeOver)}` : '';
    return `${method.label}: ${fee}${free} (${method.estimate})`;
  });
  return `Here are our delivery options:\n${lines.join('\n')}`;
}

function paymentAnswer(): string {
  return `You can pay by ${paymentMethods.map((method) => method.label.toLowerCase()).join(', ')}.`;
}

/** Picks a canned reply for a message. Pure, so it is easy to test. */
export function getMockReply(message: string): ChatReply {
  const text = message.toLowerCase();

  if (/\b(?:return|returns|exchange|refund)\b/.test(text)) {
    return {
      text: 'You can return or exchange items you are not happy with. Our Returns & Exchanges page has the full details.',
    };
  }
  if (/\b(?:ship|shipping|delivery|deliver)\b/.test(text)) return { text: shippingAnswer() };
  if (/\b(?:pay|payment|cash|card|bank)\b/.test(text)) return { text: paymentAnswer() };
  if (/\b(?:size|sizes|sizing|fit)\b/.test(text)) {
    return {
      text: 'Every product page has a size guide with body measurements in centimetres. If you are between sizes, choose the larger one for a relaxed fit.',
    };
  }

  const suggestions = pickProducts(text);
  if (suggestions.length > 0) {
    return {
      text: 'Here are a few options you might like:',
      productIds: suggestions.map((product) => product.id),
    };
  }

  if (/^\s*(?:hi|hello|hey|good (?:morning|afternoon|evening))\b/.test(text)) {
    return {
      text: 'Hello! I can help you find products, check sizes, or answer questions about delivery and returns.',
    };
  }

  return {
    text: 'I am not sure about that yet. Try asking about a product, sizes, delivery or returns, or use the Contact page to reach our team.',
  };
}
