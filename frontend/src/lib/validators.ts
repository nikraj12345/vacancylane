import { z } from "zod";

export const searchSchema = z.object({
  role: z.string().min(1, "Role is required").max(200),
  alternate_role: z.string().optional().default(""),
  location: z.string().optional().default(""),
  locations: z
    .array(
      z.object({
        label: z.string(),
        city: z.string(),
        state: z.string(),
        country: z.string(),
        remote: z.boolean(),
      })
    )
    .optional()
    .default([]),
  skills: z.string().optional().default(""),
  experience: z.string().optional().default(""),
  experience_bands: z
    .array(z.enum(["0-2", "2-5", "5-8", "8-12", "12+"]))
    .optional()
    .default([]),
  company: z.string().optional().default(""),
  sources: z.array(z.string()).min(1, "Select at least one ATS"),
  date_posted: z.enum(["any", "day", "week", "month", "year"]),
  remote_only: z.boolean(),
  employment_type: z.enum(["", "Full-time", "Part-time", "Contract"]),
  verify_live: z.boolean().optional().default(true),
  raw_results: z.boolean().optional().default(false),
});

export type SearchFormValues = z.infer<typeof searchSchema>;
