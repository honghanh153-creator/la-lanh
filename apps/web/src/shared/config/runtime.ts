import { z } from "zod";

const runtimeConfigSchema = z.object({
  VITE_API_BASE_URL: z.string().min(1).default("/v1"),
});

export const runtimeConfig = runtimeConfigSchema.parse(import.meta.env);
