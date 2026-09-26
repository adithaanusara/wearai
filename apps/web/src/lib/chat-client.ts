import { ApiError, sendChat } from '@/lib/api';
import type { ChatMessage, ChatRequest, ChatResponse } from '@/types/chat';

// What the API accepts. The API enforces them; these keep the widget from ever sending too much.
export const MAX_MESSAGE_CHARS = 1000;
export const MAX_MESSAGES = 20;
export const MAX_TOTAL_CHARS = 6000;

/** The only place the widget talks to the assistant. */
export function sendMessage(request: ChatRequest): Promise<ChatResponse> {
  return sendChat(request.messages);
}

/**
 * The part of the conversation to send: the newest messages that fit the API's limits, starting with
 * one from the customer. Notices the widget added itself are left out, and long messages are cut.
 */
export function trimHistory(messages: ChatMessage[]): ChatRequest['messages'] {
  const usable = messages
    .filter((message) => !message.error)
    .map(({ role, text }) => ({ role, text: text.slice(0, MAX_MESSAGE_CHARS) }));

  const kept: ChatRequest['messages'] = [];
  let total = 0;
  for (let i = usable.length - 1; i >= 0; i--) {
    const message = usable[i];
    if (kept.length >= MAX_MESSAGES || total + message.text.length > MAX_TOTAL_CHARS) break;
    kept.unshift(message);
    total += message.text.length;
  }
  while (kept.length > 0 && kept[0].role === 'assistant') kept.shift();
  return kept;
}

function describeWait(seconds: number): string {
  if (!Number.isFinite(seconds) || seconds <= 0) return 'a moment';
  if (seconds < 90) return `${Math.ceil(seconds)} seconds`;
  return `${Math.ceil(seconds / 60)} minutes`;
}

/** What to tell the customer when the assistant could not answer. Never shows technical details. */
export function chatErrorMessage(error: unknown): string {
  if (error instanceof ApiError) {
    if (error.code === 'rate_limited') {
      return `You are sending messages a little too quickly. Please try again in ${describeWait(Number(error.details.retryAfter))}.`;
    }
    if (error.status === 503) {
      return "The assistant isn't available right now. You can still browse the shop, or use the details on our Contact page.";
    }
    if (error.status === 422) {
      return 'That message could not be sent. Please shorten it and try again.';
    }
  }
  return 'Sorry, something went wrong. Please try again.';
}
