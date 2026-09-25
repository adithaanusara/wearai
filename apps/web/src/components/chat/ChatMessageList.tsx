import { useEffect, useRef } from 'react';
import { ChatProductCard } from '@/components/chat/ChatProductCard';
import { products } from '@/data/products';
import type { ChatMessage } from '@/types/chat';

interface ChatMessageListProps {
  messages: ChatMessage[];
  pending: boolean;
  onProductNavigate: () => void;
}

export function ChatMessageList({ messages, pending, onProductNavigate }: ChatMessageListProps) {
  const listRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const list = listRef.current;
    if (list) list.scrollTop = list.scrollHeight;
  }, [messages, pending]);

  return (
    <div
      ref={listRef}
      role="log"
      aria-live="polite"
      aria-label="Conversation"
      className="flex-1 space-y-4 overflow-y-auto p-4"
    >
      {messages.map((message) => {
        const isUser = message.role === 'user';
        const suggested = (message.productIds ?? []).flatMap((id) =>
          products.filter((product) => product.id === id),
        );

        return (
          <div
            key={message.id}
            className={`flex flex-col gap-2 ${isUser ? 'items-end' : 'items-start'}`}
          >
            <p
              className={`max-w-[85%] rounded-md px-4 py-3 text-sm whitespace-pre-line ${
                isUser ? 'bg-text text-bg' : 'bg-surface text-text'
              }`}
            >
              {message.text}
            </p>
            {suggested.length > 0 && (
              <ul className="w-full max-w-[85%] space-y-2">
                {suggested.map((product) => (
                  <li key={product.id}>
                    <ChatProductCard product={product} onNavigate={onProductNavigate} />
                  </li>
                ))}
              </ul>
            )}
          </div>
        );
      })}

      {pending && (
        <div
          role="status"
          aria-label="Assistant is typing"
          className="bg-surface flex w-fit gap-1 rounded-md px-4 py-4"
        >
          {[0, 150, 300].map((delay) => (
            <span
              key={delay}
              aria-hidden="true"
              style={{ animationDelay: `${delay}ms` }}
              className="bg-muted h-2 w-2 rounded-full motion-safe:animate-bounce"
            />
          ))}
        </div>
      )}
    </div>
  );
}
