'use client';

import Image from 'next/image';
import { useRouter } from 'next/navigation';
import { useId, useRef, useState, type ChangeEvent } from 'react';
import type { Notice } from '@/components/admin/ProductAdminPanel';
import {
  MAX_IMAGES,
  ACCEPTED_IMAGE_TYPES,
  formatFileSize,
  moveImage,
  validateImageFile,
} from '@/lib/admin-images';
import { ApiError, removeProductImage, reorderProductImages, uploadProductImage } from '@/lib/api';
import type { AdminProduct } from '@/types/api';

const smallButton =
  'border-border hover:bg-surface rounded-sm border px-3 py-2 text-xs disabled:opacity-40';

export function ProductImages({
  product,
  onNotice,
}: {
  product: AdminProduct;
  onNotice: (notice: Notice | null) => void;
}) {
  const router = useRouter();
  const inputId = useId();
  const running = useRef(false);
  const [busy, setBusy] = useState(false);
  const [file, setFile] = useState<File | null>(null);
  const [confirmingId, setConfirmingId] = useState<number | null>(null);
  const { images } = product;
  const full = images.length >= MAX_IMAGES;

  /** Runs one change, then reloads the product so the screen shows what the server now has. */
  async function run(action: () => Promise<unknown>, success: string) {
    if (running.current) return;
    running.current = true;
    setBusy(true);
    onNotice(null);
    try {
      await action();
      onNotice({ kind: 'success', text: success });
    } catch (failure) {
      onNotice({
        kind: 'error',
        text:
          failure instanceof ApiError && failure.status !== 503 && failure.status !== 500
            ? failure.message
            : 'We could not change the images. Please try again.',
      });
    } finally {
      running.current = false;
      setBusy(false);
      setConfirmingId(null);
      router.refresh();
    }
  }

  function choose(event: ChangeEvent<HTMLInputElement>) {
    const chosen = event.target.files?.[0] ?? null;
    const problem = chosen ? validateImageFile(chosen) : null;
    if (problem) {
      onNotice({ kind: 'error', text: problem });
      event.target.value = '';
      setFile(null);
      return;
    }
    onNotice(null);
    setFile(chosen);
  }

  return (
    <div className="space-y-6">
      <p className="text-muted text-xs">
        The first image is the one shoppers see first; the second shows when they hover. JPEG, PNG
        or WebP, up to 5 MB, up to {MAX_IMAGES} images.
      </p>

      <ul className="grid grid-cols-2 gap-4 sm:grid-cols-3 md:grid-cols-4">
        {images.map((image, index) => (
          <li key={image.id} className="space-y-2">
            <div className="bg-surface relative aspect-4/5 overflow-hidden">
              <Image
                src={image.url}
                alt={`${product.name}, image ${index + 1}`}
                fill
                sizes="200px"
                className="object-cover"
              />
            </div>
            <p className="text-muted text-xs">
              {index === 0 ? 'Default' : index === 1 ? 'Shown on hover' : `Image ${index + 1}`}
            </p>
            <div className="flex flex-wrap gap-2">
              <button
                type="button"
                disabled={busy || index === 0}
                className={smallButton}
                aria-label={`Move image ${index + 1} earlier`}
                onClick={() =>
                  run(
                    () =>
                      reorderProductImages(
                        product.id,
                        product.updatedAt,
                        moveImage(
                          images.map((item) => item.id),
                          index,
                          -1,
                        ),
                      ),
                    'Image moved.',
                  )
                }
              >
                ←
              </button>
              <button
                type="button"
                disabled={busy || index === images.length - 1}
                className={smallButton}
                aria-label={`Move image ${index + 1} later`}
                onClick={() =>
                  run(
                    () =>
                      reorderProductImages(
                        product.id,
                        product.updatedAt,
                        moveImage(
                          images.map((item) => item.id),
                          index,
                          1,
                        ),
                      ),
                    'Image moved.',
                  )
                }
              >
                →
              </button>
              <button
                type="button"
                disabled={busy || images.length === 1}
                className={smallButton}
                aria-label={`Remove image ${index + 1}`}
                onClick={() => {
                  if (confirmingId !== image.id) {
                    setConfirmingId(image.id);
                    return;
                  }
                  run(
                    () => removeProductImage(product.id, image.id, product.updatedAt),
                    'Image removed.',
                  );
                }}
              >
                {confirmingId === image.id ? 'Click again' : 'Remove'}
              </button>
            </div>
          </li>
        ))}
      </ul>

      {full ? (
        <p className="text-sm">This product has the most images it can have.</p>
      ) : (
        <div className="space-y-3">
          <label htmlFor={inputId} className="block text-sm">
            Add an image
          </label>
          <input
            id={inputId}
            type="file"
            accept={ACCEPTED_IMAGE_TYPES.join(',')}
            disabled={busy}
            onChange={choose}
            className="block w-full max-w-sm text-sm"
          />
          {file && (
            <p className="text-muted text-xs">
              {file.name} ({formatFileSize(file.size)})
            </p>
          )}
          <button
            type="button"
            disabled={busy || !file}
            className="bg-text text-bg rounded-sm px-6 py-3 text-xs font-medium tracking-wide uppercase disabled:opacity-40"
            onClick={() =>
              file &&
              run(() => uploadProductImage(product.id, product.updatedAt, file), 'Image added.')
            }
          >
            {busy ? 'Working…' : 'Upload image'}
          </button>
        </div>
      )}
    </div>
  );
}
