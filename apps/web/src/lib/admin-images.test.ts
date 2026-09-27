import { describe, expect, it } from 'vitest';
import { MAX_UPLOAD_BYTES, formatFileSize, moveImage, validateImageFile } from '@/lib/admin-images';

describe('validateImageFile', () => {
  it.each(['image/jpeg', 'image/png', 'image/webp'])('accepts %s', (type) => {
    expect(validateImageFile({ type, size: 1000 })).toBeNull();
  });

  it.each(['image/svg+xml', 'image/gif', 'text/html', 'application/pdf', ''])(
    'refuses %j',
    (type) => {
      expect(validateImageFile({ type, size: 1000 })).toMatch(/JPEG, PNG or WebP/);
    },
  );

  it('refuses empty and oversized files, and accepts exactly the limit', () => {
    expect(validateImageFile({ type: 'image/png', size: 0 })).toMatch(/empty/);
    expect(validateImageFile({ type: 'image/png', size: MAX_UPLOAD_BYTES + 1 })).toMatch(
      /too large/,
    );
    expect(validateImageFile({ type: 'image/png', size: MAX_UPLOAD_BYTES })).toBeNull();
  });
});

describe('moveImage', () => {
  it('swaps with the neighbour', () => {
    expect(moveImage([1, 2, 3], 1, -1)).toEqual([2, 1, 3]);
    expect(moveImage([1, 2, 3], 1, 1)).toEqual([1, 3, 2]);
  });

  it('does not move past either end, or from a bad index', () => {
    expect(moveImage([1, 2, 3], 0, -1)).toEqual([1, 2, 3]);
    expect(moveImage([1, 2, 3], 2, 1)).toEqual([1, 2, 3]);
    expect(moveImage([1, 2, 3], 5, -1)).toEqual([1, 2, 3]);
    expect(moveImage([1, 2, 3], -1, 1)).toEqual([1, 2, 3]);
  });

  it('does not change the list it was given', () => {
    const ids = [1, 2, 3];
    moveImage(ids, 0, 1);
    expect(ids).toEqual([1, 2, 3]);
  });
});

describe('formatFileSize', () => {
  it('shows kilobytes and megabytes', () => {
    expect(formatFileSize(500)).toBe('1 KB');
    expect(formatFileSize(150 * 1024)).toBe('150 KB');
    expect(formatFileSize(2.5 * 1024 * 1024)).toBe('2.5 MB');
  });
});
