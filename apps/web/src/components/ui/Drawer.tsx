'use client';

import { useEffect, useRef, type ReactNode } from 'react';
import { CloseIcon } from '@/components/ui/icons';

interface DrawerProps {
  open: boolean;
  onClose: () => void;
  title: string;
  side?: 'left' | 'right';
  children: ReactNode;
}

/** Side panel built on the native dialog element, which handles focus trapping, Escape and focus return. */
export function Drawer({ open, onClose, title, side = 'right', children }: DrawerProps) {
  const dialogRef = useRef<HTMLDialogElement>(null);

  useEffect(() => {
    const dialog = dialogRef.current;
    if (!dialog) return;
    if (open && !dialog.open) dialog.showModal();
    if (!open && dialog.open) dialog.close();
  }, [open]);

  useEffect(() => {
    if (!open) return;
    const previousOverflow = document.body.style.overflow;
    document.body.style.overflow = 'hidden';
    return () => {
      document.body.style.overflow = previousOverflow;
    };
  }, [open]);

  return (
    <dialog
      ref={dialogRef}
      aria-label={title}
      onClose={onClose}
      onClick={(event) => event.target === event.currentTarget && onClose()}
      className={`bg-bg text-text m-0 h-full max-h-none w-full max-w-sm p-0 backdrop:bg-dark/50 ${
        side === 'right' ? 'ml-auto' : 'mr-auto'
      }`}
    >
      <div className="flex h-full flex-col">
        <div className="border-border flex items-center justify-between border-b px-(--gutter) py-4">
          <h2 className="text-sm font-medium tracking-wide uppercase">{title}</h2>
          <button type="button" aria-label="Close" className="-mr-2 p-2" onClick={onClose}>
            <CloseIcon />
          </button>
        </div>
        {children}
      </div>
    </dialog>
  );
}
