import { zodResolver } from "@hookform/resolvers/zod";
import { useState } from "react";
import { useForm } from "react-hook-form";
import { Link, Navigate, useLocation, useNavigate } from "react-router";
import { z } from "zod";
import { FormField, buttonClass } from "@/components/form-field";
import { useAuth } from "@/lib/auth";

const schema = z.object({
  identifier: z.string().min(3, "Enter your email or mobile number"),
  password: z.string().min(1, "Enter your password"),
});
type Values = z.infer<typeof schema>;

export function LoginPage() {
  const { login, status } = useAuth();
  const navigate = useNavigate();
  const from = (useLocation().state as { from?: string } | null)?.from ?? "/account";
  const [error, setError] = useState<string | null>(null);
  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<Values>({ resolver: zodResolver(schema) });

  if (status === "authenticated") return <Navigate to={from} replace />;

  const onSubmit = async (v: Values) => {
    setError(null);
    try {
      await login(v.identifier, v.password);
      navigate(from, { replace: true });
    } catch (e) {
      setError(e instanceof Error ? e.message : "Something went wrong");
    }
  };

  return (
    <main className="mx-auto flex min-h-screen max-w-sm flex-col justify-center gap-6 px-6">
      <h1 className="text-2xl font-semibold text-primary">Log in</h1>
      <form onSubmit={handleSubmit(onSubmit)} className="space-y-4" noValidate>
        <FormField label="Email or mobile number" autoComplete="username" error={errors.identifier} {...register("identifier")} />
        <FormField label="Password" type="password" autoComplete="current-password" error={errors.password} {...register("password")} />
        {error && (
          <p role="alert" className="text-sm text-destructive">
            {error}
          </p>
        )}
        <button type="submit" disabled={isSubmitting} className={buttonClass}>
          {isSubmitting ? "Logging in…" : "Log in"}
        </button>
      </form>
      <p className="text-sm text-muted-foreground">
        New here?{" "}
        <Link to="/register" className="text-primary underline">
          Create an account
        </Link>
      </p>
    </main>
  );
}
