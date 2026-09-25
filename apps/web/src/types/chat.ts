export type ChatRole = 'user' | 'assistant';

/** A message as shown in the chat panel. */
export interface ChatMessage {
  id: string;
  role: ChatRole;
  text: string;
  /** Products the assistant recommends. Only ids travel over the wire; the page renders them from its catalogue. */
  productIds?: string[];
}

/** Body of POST /api/chat. */
export interface ChatRequest {
  messages: { role: ChatRole; text: string }[];
}

export interface ChatReply {
  text: string;
  productIds?: string[];
}

/** Response of POST /api/chat. */
export interface ChatResponse {
  reply: ChatReply;
}
