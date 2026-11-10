import { type ClassValue, clsx } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

const inr = new Intl.NumberFormat("en-IN", { style: "currency", currency: "INR", maximumFractionDigits: 2 });

/** Format an amount (string decimal from the API, or number) as INR. */
export function formatINR(amount: string | number): string {
  return inr.format(typeof amount === "string" ? Number(amount) : amount);
}
