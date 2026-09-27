export const MAX_IMAGES = 8;
export const MAX_UPLOAD_BYTES = 5 * 1024 * 1024;
export const ACCEPTED_IMAGE_TYPES = ['image/jpeg', 'image/png', 'image/webp'];

/**
 * A message if the file cannot be uploaded, otherwise null. This only saves a round trip: the API
 * decodes the file itself and refuses anything that is not really a JPEG, PNG or WebP.
 */
export function validateImageFile(file: { type: string; size: number }): string | null {
  if (!ACCEPTED_IMAGE_TYPES.includes(file.type)) return 'Choose a JPEG, PNG or WebP image.';
  if (file.size === 0) return 'This file is empty.';
  if (file.size > MAX_UPLOAD_BYTES) return 'The image is too large (at most 5 MB).';
  return null;
}

/** The ids with the one at `index` moved one place earlier (-1) or later (1). */
export function moveImage(ids: number[], index: number, direction: -1 | 1): number[] {
  const target = index + direction;
  if (index < 0 || index >= ids.length || target < 0 || target >= ids.length) return ids;
  const moved = [...ids];
  [moved[index], moved[target]] = [moved[target], moved[index]];
  return moved;
}

export function formatFileSize(bytes: number): string {
  if (bytes < 1024 * 1024) return `${Math.max(1, Math.round(bytes / 1024))} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}
