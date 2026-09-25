import { siteConfig } from '@/config/site';
import { formatPrice } from '@/lib/format';
import type { CheckoutOptions } from '@/types/api';

export interface FaqItem {
  question: string;
  answer: string;
}

/** Answers that quote fees or payment options are built from the same options the checkout uses. */
export function getFaqItems({ deliveryMethods, paymentMethods }: CheckoutOptions): FaqItem[] {
  const delivery = deliveryMethods
    .map((method) => {
      const fee = method.fee === 0 ? 'free' : formatPrice(method.fee);
      const free = method.freeOver !== null ? `, free over ${formatPrice(method.freeOver)}` : '';
      return `${method.label} is ${fee}${free} (${method.estimate})`;
    })
    .join('. ');

  const payments = paymentMethods.map((method) => method.label.toLowerCase()).join(', ');

  return [
    { question: 'How much does delivery cost and how long does it take?', answer: `${delivery}.` },
    { question: 'Which payment methods do you accept?', answer: `You can pay by ${payments}.` },
    {
      question: 'How do I choose my size?',
      answer:
        'Every product page has a size guide with body measurements in centimetres. If you are between sizes, choose the larger one for a relaxed fit.',
    },
    {
      question: 'How do I return or exchange an item?',
      answer: 'Our Returns & Exchanges page explains how it works and what to do next.',
    },
    {
      question: 'Can I change or cancel my order?',
      answer: `Contact us as soon as possible at ${siteConfig.contact.email} with your order reference, and we will do our best to help.`,
    },
    {
      question: 'How can I contact you?',
      answer: `Email ${siteConfig.contact.email} or call ${siteConfig.contact.phone} (${siteConfig.contact.hours}).`,
    },
  ];
}
