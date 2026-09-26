'use client';

import { useRouter } from 'next/navigation';
import { useId, useRef, useState } from 'react';
import { changeUserRole } from '@/lib/api';
import { roleChangeError, roleLabel, roles } from '@/lib/admin';
import type { Role } from '@/types/api';

interface RoleSelectProps {
  userId: number;
  email: string;
  role: Role;
  /** Your own role cannot be changed, and the API refuses it too. */
  isSelf: boolean;
}

export function RoleSelect({ userId, email, role, isSelf }: RoleSelectProps) {
  const router = useRouter();
  const selectId = useId();
  const running = useRef(false);
  const [choice, setChoice] = useState<Role>(role);
  const [error, setError] = useState('');
  const [saving, setSaving] = useState(false);

  if (isSelf) return <span className="text-muted text-xs">You</span>;

  async function save() {
    if (running.current || choice === role) return;
    running.current = true;
    setSaving(true);
    setError('');
    try {
      await changeUserRole(userId, choice);
      // Reload the list from the server, so it shows what was actually saved.
      router.refresh();
    } catch (failure) {
      setError(roleChangeError(failure));
      setChoice(role);
    } finally {
      running.current = false;
      setSaving(false);
    }
  }

  return (
    <div className="space-y-1">
      <div className="flex items-center gap-2">
        <label htmlFor={selectId} className="sr-only">
          Role for {email}
        </label>
        <select
          id={selectId}
          value={choice}
          disabled={saving}
          onChange={(event) => setChoice(event.target.value as Role)}
          className="border-border bg-bg rounded-sm border px-2 py-2 text-sm"
        >
          {roles.map((option) => (
            <option key={option} value={option}>
              {roleLabel(option)}
            </option>
          ))}
        </select>
        <button
          type="button"
          disabled={saving || choice === role}
          onClick={save}
          className="border-text hover:bg-surface rounded-sm border px-4 py-2 text-xs font-medium tracking-wide uppercase disabled:opacity-40"
        >
          {saving ? 'Saving…' : 'Save'}
        </button>
      </div>
      {error && (
        <p role="alert" className="text-error text-xs">
          {error}
        </p>
      )}
    </div>
  );
}
