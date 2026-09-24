interface Choice {
  id: string;
  label: string;
  description: string;
  /** Shown on the right, such as a price. */
  detail?: string;
}

interface ChoiceGroupProps {
  name: string;
  legend: string;
  choices: Choice[];
  value: string;
  onChange: (value: string) => void;
  error?: string;
}

export function ChoiceGroup({ name, legend, choices, value, onChange, error }: ChoiceGroupProps) {
  return (
    <fieldset>
      <legend className="mb-2 text-sm">{legend}</legend>
      <div className="space-y-2">
        {choices.map((choice) => (
          <label key={choice.id} className="block cursor-pointer">
            <input
              type="radio"
              name={name}
              value={choice.id}
              className="peer sr-only"
              checked={value === choice.id}
              onChange={() => onChange(choice.id)}
            />
            <span className="border-border peer-checked:border-text peer-focus-visible:outline-text flex items-start justify-between gap-4 rounded-sm border p-4 text-sm peer-checked:border-2 peer-focus-visible:outline-2 peer-focus-visible:outline-offset-2">
              <span>
                <span className="block font-medium">{choice.label}</span>
                <span className="text-muted mt-1 block text-xs">{choice.description}</span>
              </span>
              {choice.detail && <span className="shrink-0">{choice.detail}</span>}
            </span>
          </label>
        ))}
      </div>
      {error && <p className="text-error mt-1 text-xs">{error}</p>}
    </fieldset>
  );
}
