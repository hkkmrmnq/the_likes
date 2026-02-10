import { z } from "zod";

import { uuidSchema, dataTimeShchema } from "./base";

const ContactStatus = [
  "requested by me",
  "requested by the other user",
  "cancelled by me",
  "cancelled by the other user",
  "rejected by me",
  "rejected by the other user",
  "ongoing",
  "blocked by me",
  "blocked by the other user",
];

const nameSchema = z.string().nullable();
const statusSchema = z.enum(ContactStatus);
const distanceKmSchema = z.number().nullable();

export const durationSchema = z.string().duration(); // .iso.duration(): build error
export const nonNegativeIntSchema = z.number().int().nonnegative();

export const contactRequestSchema = z
  .object({
    user_id: uuidSchema,
    name: nameSchema,
    status: statusSchema,
    created_at: dataTimeShchema,
    time_waiting: durationSchema,
  })
  .describe("contactRequestSchema");

export const contactSchema = z.object({
  user_id: uuidSchema,
  name: nameSchema,
  status: statusSchema,
  created_at: dataTimeShchema,
  unread_messages: nonNegativeIntSchema,
});

export const contactRichSchema = z.object({
  user_id: uuidSchema,
  name: nameSchema,
  status: statusSchema,
  created_at: dataTimeShchema,
  similarity: z.number(),
  distance: distanceKmSchema,
  unread_messages: nonNegativeIntSchema,
  time_waiting: durationSchema.nullable(),
});

export const contactsArraySchema = z.array(contactRichSchema);

export const recommendationSchema = z
  .object({
    user_id: uuidSchema,
    name: nameSchema,
    similarity: z.number(),
    distance: distanceKmSchema,
  })
  .describe("recommendationSchema");

export const contactsAndRequestsSchema = z.object({
  active_contacts: contactsArraySchema,
  contact_requests: contactsArraySchema,
});

export const otherProfileSchema = z
  .object({
    user_id: uuidSchema,
    name: nameSchema,
    similarity: z.number(),
    distance: distanceKmSchema,
  })
  .describe("otherProfileSchema");

export const otherProfileResponseSchema = z
  .object({
    data: otherProfileSchema,
    message: z.string(),
  })
  .describe("otherProfileResponseSchema");

export const contactsAndRequestsResponseSchema = z
  .object({
    data: contactsAndRequestsSchema,
    message: z.string(),
  })
  .describe("contactsAndRequestsResponseSchema");

export const contsNReqstsNRecomsSchema = z
  .object({
    recommendations: z.array(recommendationSchema),
    active_contacts: contactsArraySchema,
    contact_requests: contactsArraySchema,
  })
  .describe("contsNReqstsNRecomsSchema");

export const contsNReqstsNRecomsSchemaResponseSchema = z
  .object({
    data: contsNReqstsNRecomsSchema,
    message: z.string(),
  })
  .describe("contsNReqstsNRecomsSchemaResponseSchema");

export const contactsOptionsSchema = z.object({
  cancelled_requests: contactsArraySchema,
  rejected_requests: contactsArraySchema,
  blocked_contacts: contactsArraySchema,
});

export const contactsOptionsResponseSchema = z
  .object({
    data: contactsOptionsSchema,
    message: z.string(),
  })
  .describe("contactsOptionsResponseSchema");
