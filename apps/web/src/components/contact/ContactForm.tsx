'use client';

import { useRef, useState, type FormEvent } from 'react';
import { Field, TextareaField } from '@/components/ui/Field';
import { validateContact, type ContactErrors, type ContactValues } from '@/lib/contact';

const emptyValues: ContactValues = { name: '', email: '', message: '' };
const fieldOrder: (keyof ContactValues)[] = ['name', 'email', 'message'];

export function ContactForm() {
  const formRef = useRef<HTMLFormElement>(null);
  const [values, setValues] = useState(emptyValues);
  const [errors, setErrors] = useState<ContactErrors>({});
  const [sent, setSent] = useState(false);

  function update(name: keyof ContactValues, value: string) {
    setValues((current) => ({ ...current, [name]: value }));
    setErrors((current) => ({ ...current, [name]: undefined }));
    setSent(false);
  }

  function onSubmit(event: FormEvent) {
    event.preventDefault();
    const found = validateContact(values);
    setErrors(found);

    const firstInvalid = fieldOrder.find((name) => found[name]);
    if (firstInvalid) {
      formRef.current?.querySelector<HTMLElement>(`[name="${firstInvalid}"]`)?.focus();
      return;
    }

    // Nothing is sent yet; the API endpoint replaces this in a later item.
    setValues(emptyValues);
    setSent(true);
  }

  return (
    <form ref={formRef} onSubmit={onSubmit} noValidate className="space-y-4">
      <Field
        name="name"
        label="Name"
        autoComplete="name"
        value={values.name}
        error={errors.name}
        onChange={(event) => update('name', event.target.value)}
      />
      <Field
        name="email"
        label="Email"
        type="email"
        autoComplete="email"
        value={values.email}
        error={errors.email}
        onChange={(event) => update('email', event.target.value)}
      />
      <TextareaField
        name="message"
        label="Message"
        rows={6}
        value={values.message}
        error={errors.message}
        onChange={(event) => update('message', event.target.value)}
      />
      <button
        type="submit"
        className="bg-text text-bg hover:bg-dark-2 rounded-sm px-8 py-4 text-xs font-medium tracking-wide uppercase transition-colors"
      >
        Send message
      </button>
      <p role="status" className="text-success min-h-5 text-sm">
        {sent && 'Thanks! Your message has been received.'}
      </p>
      <p className="text-muted text-xs">
        Demo only: messages are not sent until the store backend is connected.
      </p>
    </form>
  );
}
