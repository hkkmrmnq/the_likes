import { z } from "zod";
import { CONSTANTS as CNST } from "@/src/config";
import { uuidSchema } from "./base";

export const languagesSchema = z
  .array(z.enum(CNST.SUPPORTED_LANGUAGES))
  .max(
    CNST.SUPPORTED_LANGUAGES.length,
    `Only supported languages (${CNST.SUPPORTED_LANGUAGES}) can be accepted.`,
  );

export const profileWriteSchema = z
  .object({
    name: z
      .string()
      .min(1, "Name is required")
      .max(100, "Name too long")
      .nullable(),

    languages: languagesSchema,

    longitude: z
      .number()
      .min(-180, "Longitude must be ≥ -180")
      .max(180, "Longitude must be ≤ 180")
      .nullable(),

    latitude: z
      .number()
      .min(-90, "Latitude must be ≥ -90")
      .max(90, "Latitude must be ≤ 90")
      .nullable(),

    distance_limit: z
      .number()
      .min(1, "Distance must be ≥ 1 meter")
      .max(
        CNST.DISTANCE_LIMIT_MAX,
        `Distance must be ≤ ${CNST.DISTANCE_LIMIT_MAX}m`,
      )
      .nullable(),

    recommend_me: z.boolean(),
  })
  .refine(
    (data) => !(data.distance_limit && (!data.longitude || !data.latitude)),
    {
      message: "Location required to set distance limit",
      path: ["distance_limit"],
    },
  )
  .refine((data) => !(data.longitude && !data.latitude), {
    message: "To set location both latitude and longitude required",
    path: ["latitude"],
  })
  .refine((data) => !(!data.longitude && data.latitude), {
    message: "To set location both latitude and longitude required",
    path: ["longitude"],
  })
  .describe("profileWriteSchema");

export const profileReadSchema = profileWriteSchema
  .safeExtend({ user_id: uuidSchema })
  .describe("profileReadSchema");

export const profileResponseSchema = z
  .object({
    data: profileReadSchema,
    message: z.string(),
  })
  .describe("profileResponseSchema");
