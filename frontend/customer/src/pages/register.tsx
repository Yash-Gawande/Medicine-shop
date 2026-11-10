import { zodResolver } from "@hookform/resolvers/zod";
import { useState } from "react";
import { useForm } from "react-hook-form";
import { Link, Navigate, useNavigate } from "react-router";
import { z } from "zod";
import { FormField, buttonClass } from "@/components/form-field";
import { useAuth } from "@/lib/auth";

const schema = z.object({
  full_name: z.string().trim().min(2, "Enter your full name"),
  email: z.email("Enter a valid email"),
  mobile: z
    .string()
    .trim()
    .refine((v) => v === "" || /^(?:\+91|91|0)?[6-9]\d{9}$/.test(v.replace(/[\s-]/g, "")), "Enter a valid 10-digit mobile number"),
  password: z
    .string()
    .min(8, "At least 8 characters")
    .refine((v) => /[A-Za-z]/.test(v) && /\d/.test(v), "Use letters and numbers"),
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
  } = useForm<Values>({ resolver: zodResolver(schema), defaultValues: { mobile: "" } });

  if (status === "authenticated") return <Navigate to="/account" replace />;

  const onSubmit = async (v: Values) => {
    setError(null);
    try {
      await signUp({ ...v, mobile: v.mobile || undefined });
      navigate("/account", { replace: true });
    } catch (e) {
      setError(e instanceof Error ? e.message : "Something went wrong");
    }
  };

  return (
    <main className="mx-auto flex min-h-screen max-w-sm flex-col justify-center gap-6 px-6 py-10">
      <h1 className="text-2xl font-semibold text-primary">Create your account</h1>
      <form onSubmit={handleSubmit(onSubmit)} className="space-y-4" noValidate>
        <FormField label="Full name" autoComplete="name" error={errors.full_name} {...register("full_name")} />
        <FormField label="Email" type="email" autoComplete="email" error={errors.email} {...register("email")} />
        <FormField label="Mobile number (optional)" type="tel" autoComplete="tel" placeholder="98765 43210" error={errors.mobile} {...register("mobile")} />
        <FormField label="Password" type="password" autoComplete="new-password" error={errors.password} {...register("password")} />
        {error && (
          <p role="alert" className="text-sm text-destructive">
            {error}
          </p>
        )}
        <button type="submit" disabled={isSubmitting} className={buttonClass}>
          {isSubmitting ? "Creating account…" : "Sign up"}
        </button>
      </form>
      <p className="text-sm text-muted-foreground">
        Already have an account?{" "}
        <Link to="/login" className="text-primary underline">
          Log in
        </Link>
      </p>
    </main>
  );
}
