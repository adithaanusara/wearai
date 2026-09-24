'use client';

import { useState, type ComponentPropsWithoutRef } from 'react';
import { Field } from '@/components/ui/Field';

type PasswordFieldProps = Omit<ComponentPropsWithoutRef<typeof Field>, 'type' | 'endAdornment'>;

export function PasswordField(props: PasswordFieldProps) {
  const [visible, setVisible] = useState(false);

  return (
    <Field
      {...props}
      type={visible ? 'text' : 'password'}
      endAdornment={
        <button
          type="button"
          aria-pressed={visible}
          aria-label="Show password"
          className="text-xs underline"
          onClick={() => setVisible(!visible)}
        >
          {visible ? 'Hide' : 'Show'}
        </button>
      }
    />
  );
}
