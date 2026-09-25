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
  /** Content placed inside the right edge of the input, such as a show/hide button. */
  endAdornment?: ReactNode;
}

export function Field({ name, label, error, endAdornment, ...props }: FieldProps) {
  const id = `field-${name}`;
  return (
    <FieldShell id={id} label={label} error={error}>
      <div className="relative">
        <input
          id={id}
          name={name}
          aria-invalid={error ? true : undefined}
          aria-describedby={error ? `${id}-error` : undefined}
          className={`${controlClass} ${endAdornment ? 'pr-16' : ''}`}
          {...props}
        />
        {endAdornment && (
          <div className="absolute inset-y-0 right-0 flex items-center pr-3">{endAdornment}</div>
        )}
      </div>
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

interface TextareaFieldProps extends ComponentPropsWithoutRef<'textarea'> {
  name: string;
  label: string;
  error?: string;
}

export function TextareaField({ name, label, error, ...props }: TextareaFieldProps) {
  const id = `field-${name}`;
  return (
    <FieldShell id={id} label={label} error={error}>
      <textarea
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
