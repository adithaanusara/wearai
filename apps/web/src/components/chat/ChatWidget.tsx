'use client';

import { useEffect, useRef, useState, type KeyboardEvent } from 'react';
import { ChatInput } from '@/components/chat/ChatInput';
import { ChatMessageList } from '@/components/chat/ChatMessageList';
import { ChatIcon, CloseIcon } from '@/components/ui/icons';
import { siteConfig } from '@/config/site';
import { sendMessage } from '@/lib/chat-client';
import type { ChatMessage } from '@/types/chat';

const assistantName = `${siteConfig.name} Assistant`;

const suggestedPrompts = [
  'Find me a hoodie',
  'What are your delivery options?',
  'Help me choose a size',
];

const welcome: ChatMessage = {
  id: 'welcome',
  role: 'assistant',
  text: 'Hi! I can help you find products, choose a size, or answer questions about delivery and returns.',
};

const isSmallScreen = () => window.matchMedia('(max-width: 639px)').matches;

export function ChatWidget() {
  const [open, setOpen] = useState(false);
  const [messages, setMessages] = useState<ChatMessage[]>([welcome]);
  const [pending, setPending] = useState(false);
  const buttonRef = useRef<HTMLButtonElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);
  const nextId = useRef(0);
  const restoreFocus = useRef(false);

  // The panel is full screen on phones, so the page behind it should not scroll.
  useEffect(() => {
    if (!open || !isSmallScreen()) return;
    const previousOverflow = document.body.style.overflow;
    document.body.style.overflow = 'hidden';
    return () => {
      document.body.style.overflow = previousOverflow;
    };
  }, [open]);

  // Focus moves after the render, because on phones the button is hidden while the panel is open.
  useEffect(() => {
    if (open) {
      inputRef.current?.focus();
    } else if (restoreFocus.current) {
      restoreFocus.current = false;
      buttonRef.current?.focus();
    }
  }, [open]);

  function closePanel() {
    restoreFocus.current = true;
    setOpen(false);
  }

  function onKeyDown(event: KeyboardEvent) {
    if (event.key === 'Escape') closePanel();
  }

  function createId() {
    nextId.current += 1;
    return `message-${nextId.current}`;
  }

  async function send(text: string) {
    const trimmed = text.trim();
    if (!trimmed || pending) return;

    const history: ChatMessage[] = [...messages, { id: createId(), role: 'user', text: trimmed }];
    setMessages(history);
    setPending(true);

    try {
      const { reply } = await sendMessage({
        messages: history.map(({ role, text: messageText }) => ({ role, text: messageText })),
      });
      setMessages((current) => [
        ...current,
        { id: createId(), role: 'assistant', text: reply.text, productIds: reply.productIds },
      ]);
    } catch {
      setMessages((current) => [
        ...current,
        {
          id: createId(),
          role: 'assistant',
          text: 'Sorry, something went wrong. Please try again.',
        },
      ]);
    } finally {
      setPending(false);
    }
  }

  return (
    <>
      <button
        ref={buttonRef}
        type="button"
        aria-label={open ? 'Close chat' : 'Open chat'}
        aria-expanded={open}
        aria-controls="chat-panel"
        className={`bg-text text-bg hover:bg-dark-2 fixed right-4 bottom-4 z-40 h-14 w-14 items-center justify-center rounded-full transition-colors sm:right-6 sm:bottom-6 ${
          open ? 'hidden sm:flex' : 'flex'
        }`}
        onClick={() => (open ? closePanel() : setOpen(true))}
      >
        {open ? <CloseIcon /> : <ChatIcon />}
      </button>

      {open && (
        <div
          id="chat-panel"
          role="dialog"
          aria-label={assistantName}
          onKeyDown={onKeyDown}
          className="bg-bg border-border fixed inset-0 z-50 flex flex-col sm:inset-auto sm:right-6 sm:bottom-24 sm:h-[34rem] sm:max-h-[calc(100vh-8rem)] sm:w-[380px] sm:rounded-md sm:border"
        >
          <div className="border-border flex items-center justify-between border-b px-4 py-3">
            <h2 className="text-sm font-medium tracking-wide uppercase">{assistantName}</h2>
            <button
              type="button"
              aria-label="Close chat"
              className="-mr-2 p-2"
              onClick={closePanel}
            >
              <CloseIcon />
            </button>
          </div>

          <ChatMessageList
            messages={messages}
            pending={pending}
            onProductNavigate={() => isSmallScreen() && setOpen(false)}
          />

          {messages.length === 1 && (
            <ul className="flex flex-wrap gap-2 px-4 pb-3" aria-label="Suggested questions">
              {suggestedPrompts.map((prompt) => (
                <li key={prompt}>
                  <button
                    type="button"
                    className="border-border hover:bg-surface rounded-sm border px-3 py-2 text-xs"
                    onClick={() => send(prompt)}
                  >
                    {prompt}
                  </button>
                </li>
              ))}
            </ul>
          )}

          <ChatInput ref={inputRef} disabled={pending} onSend={send} />
        </div>
      )}
    </>
  );
}
