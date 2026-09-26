import type { ApiProblem } from '@/lib/api';

export interface FieldErrors<Field extends string> {
  /** One message per field. */
  fields: Partial<Record<Field, string>>;
  /** A message for anything that belongs to none of the fields. */
  other: string | null;
}

/** Puts the API's problems on the form fields they belong to. */
export function fieldErrors<Field extends string>(
  problems: ApiProblem[],
  known: readonly Field[],
): FieldErrors<Field> {
  const fields: Partial<Record<Field, string>> = {};
  let other: string | null = null;

  for (const { loc, msg } of problems) {
    const name = loc[loc.length - 1];
    if (typeof name === 'string' && (known as readonly string[]).includes(name)) {
      // The first message for a field is the most useful one.
      fields[name as Field] ??= msg;
    } else {
      other ??= msg;
    }
  }
  return { fields, other };
}

export function firstField<Field extends string>(
  fields: Partial<Record<Field, string>>,
  order: readonly Field[],
): Field | undefined {
  return order.find((field) => fields[field]);
}
