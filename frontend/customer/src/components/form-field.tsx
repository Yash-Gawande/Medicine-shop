import type { ComponentProps } from "react";
import type { FieldError } from "react-hook-form";

interface Props extends ComponentProps<"input"> {
  label: string;
  error?: FieldError;
}

export function FormField({ label, error, id, ...input }: Props) {
  const fieldId = id ?? input.name;
  return (
    <div className="space-y-1.5">
      <label htmlFor={fieldId} className="text-sm font-medium">
        {label}
      </label>
      <input
        id={fieldId}
        aria-invalid={!!error}
        aria-describedby={error ? `${fieldId}-error` : undefined}
        className="h-10 w-full rounded-md border border-border bg-background px-3 text-sm outline-none focus-visible:ring-2 focus-visible:ring-ring aria-[invalid=true]:border-destructive"
        {...input}
      />
      {error && (
        <p id={`${fieldId}-error`} className="text-xs text-destructive">
          {error.message}
        </p>
      )}
    </div>
  );
}

export const buttonClass =
  "inline-flex h-10 w-full items-center justify-center rounded-md bg-primary px-4 text-sm font-medium text-primary-foreground hover:opacity-90 disabled:opacity-50";
