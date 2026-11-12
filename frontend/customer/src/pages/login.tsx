import { zodResolver } from "@hookform/resolvers/zod";
import { FileText, ShieldCheck, Truck } from "lucide-react";
import { useState } from "react";
import { useForm } from "react-hook-form";
import { Link, Navigate, useLocation, useNavigate } from "react-router";
import { z } from "zod";
import { AuthLayout } from "@/components/auth-layout";
import { Checkbox, FormField, PasswordField, buttonClass, linkClass, outlineButtonClass } from "@/components/form-field";
import { useAuth } from "@/lib/auth";

const schema = z.object({
  identifier: z.string().min(3, "Enter your email or mobile number"),
  password: z.string().min(1, "Enter your password"),
  remember_me: z.boolean(),
});
type Values = z.infer<typeof schema>;

export const customerFeatures = [
  { icon: FileText, label: "Upload prescription" },
  { icon: ShieldCheck, label: "Genuine medicines" },
  { icon: Truck, label: "Home delivery" },
];

export function LoginPage() {
  const { login, status } = useAuth();
  const navigate = useNavigate();
  const from = (useLocation().state as { from?: string } | null)?.from ?? "/account";
  const [error, setError] = useState<string | null>(null);
  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<Values>({ resolver: zodResolver(schema), defaultValues: { remember_me: false } });

  if (status === "authenticated") return <Navigate to={from} replace />;

  const onSubmit = async (v: Values) => {
    setError(null);
    try {
      await login(v.identifier, v.password, v.remember_me);
      navigate(from, { replace: true });
    } catch (e) {
      setError(e instanceof Error ? e.message : "Something went wrong");
    }
  };

  return (
    <AuthLayout
      headline="Your health, delivered with care."
      tagline="Genuine medicines, trusted pharmacists and doorstep delivery, all in one place."
      features={customerFeatures}
    >
      <h1 className="text-[32px] font-extrabold leading-tight tracking-tight">Welcome back</h1>
      <p className="mt-2 text-sm leading-relaxed">Log in to order medicines, reorder prescriptions and track deliveries.</p>

      <form onSubmit={handleSubmit(onSubmit)} className="mt-8 space-y-5" noValidate>
        <FormField
          label="Email or mobile number"
          autoComplete="username"
          placeholder="you@example.com"
          error={errors.identifier}
          {...register("identifier")}
        />
        <PasswordField
          label="Password"
          autoComplete="current-password"
          placeholder="Enter your password"
          error={errors.password}
          {...register("password")}
        />
        <div className="flex items-center justify-between">
          <Checkbox {...register("remember_me")}>Remember me</Checkbox>
          {/* Password reset arrives with the OTP flow. */}
          <span className="cursor-not-allowed text-sm font-semibold text-primary/50" title="Coming soon">
            Forgot password?
          </span>
        </div>
        {error && (
          <p role="alert" className="text-sm font-medium text-destructive">
            {error}
          </p>
        )}
        <button type="submit" disabled={isSubmitting} className={buttonClass}>
          {isSubmitting ? "Logging in…" : "Log in"}
        </button>
      </form>

      <div className="my-5 flex items-center gap-4 text-xs text-muted-foreground">
        <span className="h-px flex-1 bg-border" />
        or
        <span className="h-px flex-1 bg-border" />
      </div>
      <button type="button" disabled title="Coming soon" className={outlineButtonClass}>
        Log in with OTP
      </button>

      <p className="mt-6 text-center text-sm">
        New to Sanjeevani?{" "}
        <Link to="/register" className={linkClass}>
          Create an account
        </Link>
      </p>
    </AuthLayout>
  );
}
