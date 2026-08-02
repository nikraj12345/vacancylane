import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function extractVariables(template: string): string[] {
  const matches = template.matchAll(/\{\{(\w+)\}\}/g);
  return [...new Set([...matches].map((m) => m[1]))];
}

export function resolveTemplate(
  template: string,
  variables: Record<string, string>
): string {
  return template.replace(/\{\{(\w+)\}\}/g, (_, key: string) => {
    return variables[key]?.trim() ? variables[key] : `{{${key}}}`;
  });
}

export function googleSearchUrl(query: string): string {
  return `https://www.google.com/search?q=${encodeURIComponent(query)}`;
}

export async function openUrlsWithDelay(
  urls: string[],
  delayMs = 500
): Promise<void> {
  for (let i = 0; i < urls.length; i++) {
    window.open(urls[i], "_blank", "noopener,noreferrer");
    if (i < urls.length - 1) {
      await new Promise((r) => setTimeout(r, delayMs));
    }
  }
}

export function formatRelative(dateStr: string | null): string {
  if (!dateStr) return "Never";
  const date = new Date(dateStr);
  const diff = Date.now() - date.getTime();
  const mins = Math.floor(diff / 60000);
  if (mins < 1) return "Just now";
  if (mins < 60) return `${mins}m ago`;
  const hours = Math.floor(mins / 60);
  if (hours < 24) return `${hours}h ago`;
  const days = Math.floor(hours / 24);
  if (days < 30) return `${days}d ago`;
  return date.toLocaleDateString();
}
