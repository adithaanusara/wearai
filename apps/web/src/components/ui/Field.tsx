import type { ComponentPropsWithoutRef, ReactNode } from 'react';

const controlClass =
  'border-border bg-bg w-full rounded-sm border px-4 py-3 text-sm aria-invalid:border-error disabled:bg-surface disabled:text-muted';

interface FieldShellProps {
  id: string;
  label: string;
  error?: string;
  children: ReactNode;
}

function FieldShell({ id, label, error, children }: FieldShellProps) {
  return (
    <div>
      <label htmlFor={id} className="mb-1 block text-sm">
        {label}
      </label>
      {children}
      {error && (
        <p id={`${id}-error`} className="text-error mt-1 text-xs">
          {error}
        </p>
      )}
    </div>
  );
}

interface FieldProps extends ComponentPropsWithoutRef<'input'> {
  name: string;
  label: string;
  error?: string;
}

export function Field({ name, label, error, ...props }: FieldProps) {
  const id = `field-${name}`;
  return (
    <FieldShell id={id} label={label} error={error}>
      <input
        id={id}
        name={name}
        aria-invalid={error ? true : undefined}
        aria-describedby={error ? `${id}-error` : undefined}
        className={controlClass}
        {...props}
      />
    </FieldShell>
  );
}

interface SelectFieldProps extends ComponentPropsWithoutRef<'select'> {
  name: string;
  label: string;
  error?: string;
}

export function SelectField({ name, label, error, children, ...props }: SelectFieldProps) {
  const id = `field-${name}`;
  return (
    <FieldShell id={id} label={label} error={error}>
      <select
        id={id}
        name={name}
        aria-invalid={error ? true : undefined}
        aria-describedby={error ? `${id}-error` : undefined}
        className={controlClass}
        {...props}
      >
        {children}
      </select>
    </FieldShell>
  );
}
