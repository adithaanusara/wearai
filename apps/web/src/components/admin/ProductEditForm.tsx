'use client';

import { useRouter } from 'next/navigation';
import { useRef, useState, type FormEvent } from 'react';
import { Field } from '@/components/ui/Field';
import {
  PRODUCT_FIELDS,
  formValuesFor,
  toProductEdit,
  validateProductForm,
  type ProductField,
} from '@/lib/admin-products';
import { ApiError, editProduct } from '@/lib/api';
import { fieldErrors, firstField } from '@/lib/form-errors';
import type { Notice } from '@/components/admin/ProductAdminPanel';
import type { AdminProduct } from '@/types/api';

export function ProductEditForm({
  product,
  onNotice,
}: {
  product: AdminProduct;
  onNotice: (notice: Notice | null) => void;
}) {
  const router = useRouter();
  const running = useRef(false);
  const [values, setValues] = useState(() => formValuesFor(product));
  const [errors, setErrors] = useState<Partial<Record<ProductField, string>>>({});
  const [saving, setSaving] = useState(false);

  function update(field: ProductField, value: string) {
    setValues((current) => ({ ...current, [field]: value }));
  }

  function focusField(field: ProductField | undefined) {
    if (field) document.getElementById(`field-${field}`)?.focus();
  }

  async function submit(event: FormEvent) {
    event.preventDefault();
    if (running.current) return;

    const problems = validateProductForm(values);
    setErrors(problems);
    onNotice(null);
    if (Object.keys(problems).length > 0) {
      focusField(firstField(problems, PRODUCT_FIELDS));
      return;
    }

    running.current = true;
    setSaving(true);
    try {
      await editProduct(product.id, product.updatedAt, toProductEdit(values));
      onNotice({ text: 'Saved.', kind: 'success' });
      router.refresh();
    } catch (failure) {
      if (failure instanceof ApiError && failure.status === 422) {
        const { fields, other } = fieldErrors(failure.problems, PRODUCT_FIELDS);
        setErrors(fields);
        onNotice(other ? { text: other, kind: 'error' } : null);
        focusField(firstField(fields, PRODUCT_FIELDS));
      } else if (failure instanceof ApiError && failure.code === 'stale_product') {
        onNotice({ text: failure.message, kind: 'error' });
        // Load the newer version, so the next save is based on it.
        router.refresh();
      } else {
        onNotice({ text: 'We could not save the product. Please try again.', kind: 'error' });
      }
    } finally {
      running.current = false;
      setSaving(false);
    }
  }

  return (
    <form onSubmit={submit} noValidate className="max-w-xl space-y-5">
      <Field
        name="name"
        label="Name"
        value={values.name}
        maxLength={120}
        error={errors.name}
        onChange={(event) => update('name', event.target.value)}
      />
      <Field
        name="price"
        label="Price (LKR, whole rupees)"
        inputMode="numeric"
        value={values.price}
        error={errors.price}
        onChange={(event) => update('price', event.target.value)}
      />
      <Field
        name="compareAtPrice"
        label="Compare-at price (LKR, optional, shown crossed out)"
        inputMode="numeric"
        value={values.compareAtPrice}
        error={errors.compareAtPrice}
        onChange={(event) => update('compareAtPrice', event.target.value)}
      />
      <div>
        <label htmlFor="field-description" className="mb-1 block text-sm">
          Description
        </label>
        <textarea
          id="field-description"
          name="description"
          rows={6}
          maxLength={2000}
          value={values.description}
          aria-invalid={errors.description ? true : undefined}
          aria-describedby={errors.description ? 'field-description-error' : undefined}
          onChange={(event) => update('description', event.target.value)}
          className="border-border bg-bg aria-invalid:border-error w-full rounded-sm border px-4 py-3 text-sm"
        />
        {errors.description && (
          <p id="field-description-error" className="text-error mt-1 text-xs">
            {errors.description}
          </p>
        )}
      </div>

      <div className="flex flex-wrap items-center gap-4">
        <button
          type="submit"
          disabled={saving}
          className="bg-text text-bg rounded-sm px-8 py-3 text-xs font-medium tracking-wide uppercase disabled:opacity-40"
        >
          {saving ? 'Saving…' : 'Save changes'}
        </button>
      </div>
    </form>
  );
}
