import { Plus } from "lucide-react";

export const BRAND_NAME = "Sanjeevani Pharmacy";

export function Logo({ className = "" }: { className?: string }) {
  return (
    <div className={`flex items-center gap-3 ${className}`}>
      <span className="flex size-11 items-center justify-center rounded-xl bg-primary text-primary-foreground">
        <Plus className="size-6" strokeWidth={3} aria-hidden />
      </span>
      <span className="text-lg font-semibold">{BRAND_NAME}</span>
    </div>
  );
}
