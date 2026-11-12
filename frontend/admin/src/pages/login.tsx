import { zodResolver } from "@hookform/resolvers/zod";
import { ClipboardList, FileText, Package } from "lucide-react";
import { useState } from "react";
import { useForm } from "react-hook-form";
import { Navigate, useLocation, useNavigate } from "react-router";
import { z } from "zod";
import { AuthLayout } from "@/components/auth-layout";
import { Checkbox, FormField, PasswordField, buttonClass } from "@/components/form-field";
import { useAuth } from "@/lib/auth";

const schema = z.object({
  identifier: z.string().min(3, "Enter your email"),
  password: z.string().min(1, "Enter your password"),
  remember_me: z.boolean(),
});
type Values = z.infer<typeof schema>;

const features = [
  { icon: ClipboardList, label: "Manage orders" },
  { icon: FileText, label: "Review prescriptions" },
  { icon: Package, label: "Track inventory" },
];

export function LoginPage() {
  const { login, logout, status, user } = useAuth();
  const navigate = useNavigate();
  const from = (useLocation().state as { from?: string } | null)?.from ?? "/";
  const [error, setError] = useState<string | null>(null);
  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<Values>({ resolver: zodResolver(schema), defaultValues: { remember_me: false } });

  if (status === "authenticated" && user?.user_type === "staff") return <Navigate to={from} replace />;

  const onSubmit = async (v: Values) => {
    setError(null);
    try {
      const signedIn = await login(v.identifier, v.password, v.remember_me);
      if (signedIn.user_type !== "staff") {
        await logout();
        setError("This account does not have admin access");
        return;
      }
      navigate(from, { replace: true });
    } catch (e) {
      setError(e instanceof Error ? e.message : "Something went wrong");
    }
  };

  return (
    <AuthLayout
      headline="Run the pharmacy with confidence."
      tagline="Orders, prescriptions, stock and deliveries, managed from one secure console."
      features={features}
    >
      <h1 className="text-[32px] font-extrabold leading-tight tracking-tight">Admin sign in</h1>
      <p className="mt-2 text-sm leading-relaxed">Sign in with your staff account to manage the pharmacy.</p>

      <form onSubmit={handleSubmit(onSubmit)} className="mt-8 space-y-5" noValidate>
        <FormField
          label="Email"
          type="email"
          autoComplete="username"
          placeholder="you@pharmacy.com"
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
        <Checkbox {...register("remember_me")}>Keep me signed in on this device</Checkbox>
        {error && (
          <p role="alert" className="text-sm font-medium text-destructive">
            {error}
          </p>
        )}
        <button type="submit" disabled={isSubmitting} className={buttonClass}>
          {isSubmitting ? "Signing in…" : "Sign in"}
        </button>
      </form>
    </AuthLayout>
  );
}
