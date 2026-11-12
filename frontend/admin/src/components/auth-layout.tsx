import type { LucideIcon } from "lucide-react";
import type { ReactNode } from "react";
import { AuthIllustration } from "@/components/auth-illustration";
import { Logo } from "@/components/logo";

export interface AuthFeature {
  icon: LucideIcon;
  label: string;
}

interface Props {
  /** Left-panel headline and supporting copy. */
  headline: string;
  tagline: string;
  features: AuthFeature[];
  children: ReactNode;
}

/** Split screen: brand panel (lg+) beside the form. Below lg only the form shows, under a compact logo. */
export function AuthLayout({ headline, tagline, features, children }: Props) {
  return (
    <div className="grid min-h-screen lg:grid-cols-[minmax(0,15fr)_minmax(0,17fr)]">
      <aside className="hidden flex-col justify-between bg-foreground px-14 py-14 text-background lg:flex">
        <Logo />
        <div>
          <AuthIllustration className="mb-10 w-full max-w-md" />
          <h2 className="max-w-md text-4xl font-extrabold leading-tight tracking-tight">{headline}</h2>
          <p className="mt-4 max-w-md text-base leading-relaxed text-background/75">{tagline}</p>
        </div>
        <ul className="flex gap-12 text-sm font-semibold">
          {features.map(({ icon: Icon, label }) => (
            <li key={label} className="flex max-w-28 items-start gap-2.5">
              <Icon className="mt-0.5 size-4 shrink-0 text-primary" aria-hidden />
              {label}
            </li>
          ))}
        </ul>
      </aside>
      <main className="flex items-center justify-center px-6 py-12">
        <div className="w-full max-w-[400px]">
          <Logo className="mb-10 lg:hidden" />
          {children}
        </div>
      </main>
    </div>
  );
}
