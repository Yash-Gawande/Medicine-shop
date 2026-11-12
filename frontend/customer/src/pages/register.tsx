import { zodResolver } from "@hookform/resolvers/zod";
import { useState } from "react";
import { useForm } from "react-hook-form";
import { Link, Navigate, useNavigate } from "react-router";
import { z } from "zod";
import { AuthLayout } from "@/components/auth-layout";
import { Checkbox, FormField, PasswordField, buttonClass, linkClass } from "@/components/form-field";
import { useAuth } from "@/lib/auth";
import { customerFeatures } from "@/pages/login";

const schema = z.object({
  full_name: z.string().trim().min(2, "Enter your full name"),
  mobile: z
    .string()
    .trim()
    .refine((v) => v === "" || /^(?:\+91|91|0)?[6-9]\d{9}$/.test(v.replace(/[\s-]/g, "")), "Enter a valid 10-digit mobile number"),
  email: z.email("Enter a valid email"),
  password: z
    .string()
    .min(8, "At least 8 characters")
    .refine((v) => /[A-Za-z]/.test(v) && /\d/.test(v), "Use letters and numbers"),
  terms: z.boolean().refine((v) => v, "Please accept the Terms and Privacy Policy"),
});
type Values = z.infer<typeof schema>;

export function RegisterPage() {
  const { register: signUp, status } = useAuth();
  const navigate = useNavigate();
  const [error, setError] = useState<string | null>(null);
  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<Values>({ resolver: zodResolver(schema), defaultValues: { mobile: "", terms: false } });

  if (status === "authenticated") return <Navigate to="/account" replace />;

  const onSubmit = async ({ terms: _terms, ...v }: Values) => {
    setError(null);
    try {
      await signUp({ ...v, mobile: v.mobile.replace(/[\s-]/g, "") || undefined });
      navigate("/account", { replace: true });
    } catch (e) {
      setError(e instanceof Error ? e.message : "Something went wrong");
    }
  };

  return (
    <AuthLayout
      headline="Join in under a minute."
      tagline="Create an account to save prescriptions, reorder in one tap and track every delivery."
      features={customerFeatures}
    >
      <h1 className="text-[32px] font-extrabold leading-tight tracking-tight">Create your account</h1>
      <p className="mt-2 text-sm leading-relaxed">Register to upload prescriptions and get medicines delivered home.</p>

      <form onSubmit={handleSubmit(onSubmit)} className="mt-6 space-y-4" noValidate>
        <FormField label="Full name" autoComplete="name" placeholder="Your full name" error={errors.full_name} {...register("full_name")} />
        <FormField label="Mobile number" type="tel" autoComplete="tel" placeholder="+91 00000 00000" error={errors.mobile} {...register("mobile")} />
        <FormField label="Email" type="email" autoComplete="email" placeholder="you@example.com" error={errors.email} {...register("email")} />
        <PasswordField
          label="Password"
          autoComplete="new-password"
          placeholder="Create a password"
          hint="At least 8 characters"
          error={errors.password}
          {...register("password")}
        />
        <div>
          <Checkbox {...register("terms")}>
            <span>
              I agree to the{" "}
              <Link to="/terms" className={linkClass}>
                Terms
              </Link>{" "}
              and{" "}
              <Link to="/privacy" className={linkClass}>
                Privacy Policy
              </Link>
            </span>
          </Checkbox>
          {errors.terms && <p className="mt-1 text-xs text-destructive">{errors.terms.message}</p>}
        </div>
        {error && (
          <p role="alert" className="text-sm font-medium text-destructive">
            {error}
          </p>
        )}
        <button type="submit" disabled={isSubmitting} className={buttonClass}>
          {isSubmitting ? "Creating account…" : "Create account"}
        </button>
      </form>

      <p className="mt-5 text-center text-sm">
        Already registered?{" "}
        <Link to="/login" className={linkClass}>
          Log in
        </Link>
      </p>
    </AuthLayout>
  );
}
