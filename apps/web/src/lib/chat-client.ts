import { getMockReply } from '@/lib/chat-mock';
import type { ChatRequest, ChatResponse } from '@/types/chat';

const MOCK_DELAY_MS = 900;

/**
 * The only place the widget talks to an assistant. It answers locally for now;
 * once the backend exists this becomes a POST to /api/chat with the same request and response types.
 */
export async function sendMessage(request: ChatRequest): Promise<ChatResponse> {
  const lastUserMessage = [...request.messages]
    .reverse()
    .find((message) => message.role === 'user');

  // The delay lets the typing indicator show, like a real network call would.
  await new Promise((resolve) => setTimeout(resolve, MOCK_DELAY_MS));
  return { reply: getMockReply(lastUserMessage?.text ?? '') };
}
