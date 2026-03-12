import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function formatNumber(value: number) {
  return new Intl.NumberFormat("en-US").format(value);
}

export function sanitizeInput(value: string) {
  return value.replace(/[<>]/g, "").trim();
}
