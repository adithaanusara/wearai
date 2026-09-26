import { describe, expect, it } from 'vitest';
import { ApiError } from '@/lib/api';
import { actionLabel, describeChange, hasRole, roleChangeError, roleLabel } from '@/lib/admin';
import { formatDateTime } from '@/lib/format';

describe('hasRole', () => {
  it('orders customer < staff < admin', () => {
    expect(hasRole('admin', 'staff')).toBe(true);
    expect(hasRole('staff', 'staff')).toBe(true);
    expect(hasRole('staff', 'admin')).toBe(false);
    expect(hasRole('customer', 'staff')).toBe(false);
  });

  it('gives nobody access when there is no role', () => {
    expect(hasRole(undefined, 'staff')).toBe(false);
  });
});

describe('labels', () => {
  it('capitalises roles', () => expect(roleLabel('staff')).toBe('Staff'));
  it('turns an action into words', () =>
    expect(actionLabel('user.role_changed')).toBe('User role changed'));
});

describe('describeChange', () => {
  it('summarises a role change', () => {
    expect(describeChange({ email: 'a@b.lk', from: 'customer', to: 'staff' })).toBe(
      'a@b.lk: customer → staff',
    );
  });

  it('is empty for anything else', () => {
    expect(describeChange({ note: 1 })).toBe('');
    expect(describeChange({ from: 1, to: 2 })).toBe('');
  });
});

describe('roleChangeError', () => {
  it('shows the API reason', () => {
    expect(roleChangeError(new ApiError(409, 'You cannot change your own role.'))).toBe(
      'You cannot change your own role.',
    );
  });

  it('hides generic failures behind a friendly message', () => {
    expect(roleChangeError(new ApiError(500, 'Request failed (500)'))).toMatch(/could not change/);
    expect(roleChangeError('nope')).toMatch(/could not change/);
  });
});

describe('formatDateTime', () => {
  it('always uses UTC', () => {
    expect(formatDateTime('2026-09-12T14:05:00Z')).toBe('12 Sept 2026, 14:05 UTC');
  });
});
