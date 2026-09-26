import { forwardRef, useState, type FormEvent } from 'react';
import { SendIcon } from '@/components/ui/icons';
import { MAX_MESSAGE_CHARS } from '@/lib/chat-client';

interface ChatInputProps {
  disabled: boolean;
  onSend: (text: string) => void;
}

export const ChatInput = forwardRef<HTMLInputElement, ChatInputProps>(function ChatInput(
  { disabled, onSend },
  ref,
) {
  const [text, setText] = useState('');
  const canSend = text.trim().length > 0 && !disabled;

  function onSubmit(event: FormEvent) {
    event.preventDefault();
    if (!canSend) return;
    onSend(text);
    setText('');
  }

  return (
    <form onSubmit={onSubmit} className="border-border flex items-center gap-2 border-t p-3">
      <label htmlFor="chat-input" className="sr-only">
        Message
      </label>
      <input
        ref={ref}
        id="chat-input"
        type="text"
        value={text}
        autoComplete="off"
        maxLength={MAX_MESSAGE_CHARS}
        placeholder="Type your message…"
        className="border-border bg-bg min-w-0 flex-1 rounded-sm border px-3 py-3 text-sm"
        onChange={(event) => setText(event.target.value)}
      />
      <button
        type="submit"
        aria-label="Send message"
        disabled={!canSend}
        className="bg-text text-bg flex h-11 w-11 shrink-0 items-center justify-center rounded-sm disabled:opacity-40"
      >
        <SendIcon />
      </button>
    </form>
  );
});
