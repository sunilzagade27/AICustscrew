import type { FormEvent } from "react";

interface InputsFormProps {
  symptom: string;
  error: string | null;
  disabled: boolean;
  onSymptomChange: (value: string) => void;
  onSubmit: () => void;
}

export function InputsForm({
  symptom,
  error,
  disabled,
  onSymptomChange,
  onSubmit,
}: InputsFormProps) {
  function handleSubmit(event: FormEvent) {
    event.preventDefault();
    onSubmit();
  }

  return (
    <section className="panel" aria-labelledby="inputs-heading">
      <h2 id="inputs-heading">Inputs</h2>
      <p className="muted">
        Paste an alert or describe the symptom to start a Critical Research run.
      </p>
      <form onSubmit={handleSubmit}>
        <label htmlFor="symptom">Symptom / alert</label>
        <textarea
          id="symptom"
          name="symptom"
          rows={6}
          maxLength={8192}
          value={symptom}
          disabled={disabled}
          onChange={(e) => onSymptomChange(e.target.value)}
          placeholder="e.g. API response times have degraded 3x in the last hour"
        />
        {error ? (
          <p className="error" role="alert">
            {error}
          </p>
        ) : null}
        <button type="submit" disabled={disabled}>
          Start research run
        </button>
      </form>
    </section>
  );
}
