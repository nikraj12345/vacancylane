export const EXPERIENCE_OPTIONS = [
  {
    id: "0-2",
    label: "0–2 years",
    minYears: 0,
    maxYears: 2,
  },
  {
    id: "2-5",
    label: "2–5 years",
    minYears: 2,
    maxYears: 5,
  },
  {
    id: "5-8",
    label: "5–8 years",
    minYears: 5,
    maxYears: 8,
  },
  {
    id: "8-12",
    label: "8–12 years",
    minYears: 8,
    maxYears: 12,
  },
  {
    id: "12+",
    label: "12+ years",
    minYears: 12,
    maxYears: 50,
  },
] as const;

export type ExperienceBandId = (typeof EXPERIENCE_OPTIONS)[number]["id"];

export function experienceLabels(ids: string[]): string {
  return EXPERIENCE_OPTIONS.filter((option) => ids.includes(option.id))
    .map((option) => option.label)
    .join(", ");
}
