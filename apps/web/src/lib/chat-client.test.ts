import { describe, expect, it } from 'vitest';
import { ApiError } from '@/lib/api';
import {
  MAX_MESSAGE_CHARS,
  MAX_MESSAGES,
  MAX_TOTAL_CHARS,
  chatErrorMessage,
  trimHistory,
} from '@/lib/chat-client';
import type { ChatMessage } from '@/types/chat';

let counter = 0;
const message = (role: ChatMessage['role'], text: string, extra: Partial<ChatMessage> = {}) =>
  ({ id: `m${counter++}`, role, text, ...extra }) satisfies ChatMessage;

describe('trimHistory', () => {
  it("drops the widget's greeting, so the conversation starts with the customer", () => {
    const history = [message('assistant', 'Hi!'), message('user', 'Show hoodies')];

    expect(trimHistory(history)).toEqual([{ role: 'user', text: 'Show hoodies' }]);
  });

  it('keeps the whole conversation when it is short, in order', () => {
    const history = [
      message('user', 'Hi'),
      message('assistant', 'Hello!'),
      message('user', 'Delivery cost?'),
    ];

    expect(trimHistory(history).map((m) => m.role)).toEqual(['user', 'assistant', 'user']);
  });

  it('never sends the notices the widget added itself', () => {
    const history = [
      message('user', 'one'),
      message('assistant', 'The assistant is unavailable.', { error: true }),
      message('user', 'two'),
    ];

    expect(trimHistory(history).map((m) => m.text)).toEqual(['one', 'two']);
  });

  it('keeps only the newest messages when there are too many', () => {
    const history = Array.from({ length: 30 }, (_, i) =>
      message(i % 2 === 0 ? 'user' : 'assistant', `turn ${i}`),
    );
    history.push(message('user', 'the newest question'));

    const sent = trimHistory(history);

    expect(sent.length).toBeLessThanOrEqual(MAX_MESSAGES);
    expect(sent[0].role).toBe('user');
    expect(sent.at(-1)?.text).toBe('the newest question');
  });

  it('keeps the total size within the limit', () => {
    const history = Array.from({ length: 10 }, (_, i) =>
      message(i % 2 === 0 ? 'user' : 'assistant', 'x'.repeat(900)),
    );
    history.push(message('user', 'latest'));

    const sent = trimHistory(history);

    expect(sent.reduce((total, m) => total + m.text.length, 0)).toBeLessThanOrEqual(
      MAX_TOTAL_CHARS,
    );
    expect(sent[0].role).toBe('user');
    expect(sent.at(-1)?.text).toBe('latest');
  });

  it('cuts a very long message so the API does not reject it', () => {
    const history = [
      message('user', 'q'),
      message('assistant', 'a'.repeat(1200)),
      message('user', 'next'),
    ];

    const sent = trimHistory(history);

    expect(sent.every((m) => m.text.length <= MAX_MESSAGE_CHARS)).toBe(true);
    expect(sent[1].text).toHaveLength(MAX_MESSAGE_CHARS);
  });

  it('always keeps the message the customer just sent', () => {
    expect(trimHistory([message('user', 'only this')])).toEqual([
      { role: 'user', text: 'only this' },
    ]);
  });

  it('sends nothing for an empty conversation', () => {
    expect(trimHistory([])).toEqual([]);
  });
});

describe('chatErrorMessage', () => {
  const limited = (retryAfter: unknown) =>
    new ApiError(429, 'raw', [], { code: 'rate_limited', details: { retryAfter } });

  it('says how long to wait when rate limited', () => {
    expect(chatErrorMessage(limited(45))).toContain('45 seconds');
    expect(chatErrorMessage(limited(600))).toContain('10 minutes');
    expect(chatErrorMessage(limited(90))).toContain('2 minutes');
  });

  it('copes with a missing or odd wait time', () => {
    for (const value of [undefined, 'soon', NaN, 0, -5]) {
      expect(chatErrorMessage(limited(value))).toContain('a moment');
    }
  });

  it('explains that the assistant is unavailable, and that the shop still works', () => {
    const message = chatErrorMessage(new ApiError(503, 'The store service is unavailable.'));

    expect(message).toMatch(/isn't available/);
    expect(message).toMatch(/browse the shop/);
  });

  it('asks for a shorter message after a validation error', () => {
    expect(chatErrorMessage(new ApiError(422, 'x', [{ loc: ['body'], msg: 'y' }]))).toMatch(
      /shorten/,
    );
  });

  it('falls back to a generic apology, never showing technical details', () => {
    for (const error of [
      new ApiError(500, 'Traceback: secret internal detail'),
      new Error('secret internal detail'),
      'a string',
      null,
    ]) {
      const message = chatErrorMessage(error);
      expect(message).toBe('Sorry, something went wrong. Please try again.');
      expect(message).not.toContain('secret');
    }
  });
});
