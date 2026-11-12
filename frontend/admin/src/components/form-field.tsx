import { Eye, EyeOff } from "lucide-react";
import { type ComponentProps, type ReactNode, useState } from "react";
import type { FieldError } from "react-hook-form";

type InputProps = ComponentProps<"input">;

interface FieldProps extends Omit<InputProps, "children"> {
  label: string;
  error?: FieldError;
  hint?: string;
}

const inputClass =
  "h-[52px] w-full rounded-lg border border-foreground/30 bg-muted px-4 text-sm outline-none placeholder:text-muted-foreground focus-visible:border-primary focus-visible:ring-2 focus-visible:ring-ring/40 aria-[invalid=true]:border-destructive";

function Field({
  label,
  error,
  hint,
  id,
  render,
  ...input
}: FieldProps & { render: (props: InputProps) => ReactNode }) {
  const fieldId = id ?? input.name;
  const describedBy = error ? `${fieldId}-error` : hint ? `${fieldId}-hint` : undefined;
  return (
    <div className="space-y-2">
      <label htmlFor={fieldId} className="text-sm font-semibold">
        {label}
      </label>
      {render({ id: fieldId, "aria-invalid": !!error, "aria-describedby": describedBy, className: inputClass, ...input })}
      {error ? (
        <p id={`${fieldId}-error`} className="text-xs text-destructive">
          {error.message}
        </p>
      ) : hint ? (
        <p id={`${fieldId}-hint`} className="text-xs text-muted-foreground">
          {hint}
        </p>
      ) : null}
    </div>
  );
}

export function FormField(props: FieldProps) {
  return <Field {...props} render={(p) => <input {...p} />} />;
}

export function PasswordField(props: FieldProps) {
  const [visible, setVisible] = useState(false);
  return (
    <Field
      {...props}
      render={(p) => (
        <div className="relative">
          <input {...p} type={visible ? "text" : "password"} className={`${inputClass} pr-12`} />
          <button
            type="button"
            onClick={() => setVisible((v) => !v)}
            aria-label={visible ? "Hide password" : "Show password"}
            className="absolute inset-y-0 right-0 flex w-12 items-center justify-center text-foreground"
          >
            {visible ? <EyeOff className="size-5" /> : <Eye className="size-5" />}
          </button>
        </div>
      )}
    />
  );
}

export function Checkbox({ children, ...input }: InputProps) {
  return (
    <label className="flex items-center gap-2.5 text-sm">
      <input type="checkbox" className="size-[18px] rounded border-foreground/40 accent-primary" {...input} />
      {children}
    </label>
  );
}

export const linkClass = "font-semibold text-primary underline underline-offset-2 hover:opacity-80";
export const buttonClass =
  "inline-flex h-[54px] w-full items-center justify-center rounded-lg bg-primary px-4 text-sm font-semibold text-primary-foreground hover:opacity-90 disabled:opacity-50";
export const outlineButtonClass =
  "inline-flex h-[54px] w-full items-center justify-center rounded-lg border border-foreground bg-transparent px-4 text-sm font-semibold hover:bg-accent disabled:opacity-50";
