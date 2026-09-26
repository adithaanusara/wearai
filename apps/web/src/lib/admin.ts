import type { Role } from '@/types/api';

const rank: Record<Role, number> = { customer: 0, staff: 1, admin: 2 };

export const roles: Role[] = ['customer', 'staff', 'admin'];

/** Whether a role is at least the minimum. Only decides what to show; the API enforces access. */
export function hasRole(role: Role | undefined, minimum: Role): boolean {
  return role !== undefined && rank[role] >= rank[minimum];
}

export function roleLabel(role: string): string {
  return role.charAt(0).toUpperCase() + role.slice(1);
}

/** "user.role_changed" -> "User role changed". */
export function actionLabel(action: string): string {
  const text = action.replace(/[._]/g, ' ').trim();
  return text.charAt(0).toUpperCase() + text.slice(1);
}

/** A short plain-language summary of an audit entry's details, or an empty string. */
export function describeChange(details: Record<string, unknown>): string {
  const { email, from, to } = details;
  if (typeof from === 'string' && typeof to === 'string') {
    const who = typeof email === 'string' ? `${email}: ` : '';
    return `${who}${from} → ${to}`;
  }
  return '';
}

/** The message to show when changing a role fails. */
export function roleChangeError(error: unknown): string {
  const message = error instanceof Error ? error.message : '';
  return message && !message.startsWith('Request failed')
    ? message
    : 'We could not change the role. Please try again.';
}
