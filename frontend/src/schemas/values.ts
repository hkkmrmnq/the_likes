import { z } from "zod";
import { CONSTANTS as CNST } from "@/src/config";

export const attitudeReadSchema = z
  .object({
    attitude_id: z.number().int().positive(),
    statement: z.string(),
    chosen: z.boolean(),
  })
  .describe("attitudeSchema");

const aspectIdField = z.number().int().positive({
  message: "Aspect ID must be a positive integer",
});

const numberOfValuesMessage = `User order must be from 1 to ${CNST.NUMBER_OF_VALUES} (number of values)`;

const aspectReadSchema = z
  .object({
    aspect_id: aspectIdField,
    aspect_key_phrase: z.string(),
    aspect_statement: z.string(),
    included: z.boolean(),
  })
  .describe("aspectReadSchema");

export type AspectRead = z.infer<typeof aspectReadSchema>;

const aspectSubmitSchema = z
  .object({
    aspect_id: aspectIdField,
    included: z.boolean(),
  })
  .describe("aspectSubmitSchema");

export type AspectSubmit = z.infer<typeof aspectSubmitSchema>;

const valueBaseShape = {
  value_id: z.number().int().positive({
    message: "Value ID must be a positive integer",
  }),
  polarity: z.enum(["positive", "neutral", "negative"], {
    message: "Polarity must be 'positive' / 'neutral' / 'negative'",
  }),
  user_order: z
    .number()
    .int()
    .min(1, { message: numberOfValuesMessage })
    .max(CNST.NUMBER_OF_VALUES, { message: numberOfValuesMessage }),
};

function checkAspectsUniquiness(aspects: AspectRead[] | AspectSubmit[]) {
  const aspectIds = aspects.map((a) => a.aspect_id);
  const uniqueIds = new Set(aspectIds);
  return aspectIds.length === uniqueIds.size;
}

const valueReadShape = {
  value_name: z.string(),
  aspects: z
    .array(aspectReadSchema)
    .refine((aspects) => checkAspectsUniquiness(aspects), {
      message: "Aspect IDs must be unique",
    }),
};

export const valueReadSchema = z
  .object({
    ...valueBaseShape,
    ...valueReadShape,
  })
  .describe("valueReadSchema");

export type ValueRead = z.infer<typeof valueReadSchema>;

const valueSubmitShape = {
  aspects: z
    .array(aspectSubmitSchema)
    .refine((aspects) => checkAspectsUniquiness(aspects), {
      message: "Aspect IDs must be unique",
    }),
};

export const valueSubmitSchema = z
  .object({
    ...valueBaseShape,
    ...valueSubmitShape,
  })
  .describe("valueSubmitSchema");

export type ValueSubmit = z.infer<typeof valueSubmitSchema>;

function checkValueIDsUniqueness(values: ValueRead[] | ValueSubmit[]) {
  const valueIds = values.map((v) => v.value_id);
  const uniqueIds = new Set(valueIds);
  return valueIds.length === uniqueIds.size;
}

function checkUserOrder(values: ValueRead[] | ValueSubmit[]) {
  const userOrders = values.map((v) => v.user_order);
  const uniqueOrders = new Set(userOrders);
  return userOrders.length === uniqueOrders.size;
}

export const valuesArray = z
  .array(valueReadSchema)
  .length(CNST.NUMBER_OF_VALUES, { message: "Unexpected number of values." })
  .refine((valueLinks) => checkValueIDsUniqueness(valueLinks), {
    message: "Value IDs must be unique",
  })
  .refine(
    (valueLinks) => {
      return checkUserOrder(valueLinks);
    },
    { message: "User order values must be unique" }
  );

export const valuesSubmitArray = z
  .array(valueSubmitSchema)
  .length(CNST.NUMBER_OF_VALUES, { message: "Unexpected number of values." })
  .refine((valueLinks) => checkValueIDsUniqueness(valueLinks), {
    message: "Value IDs must be unique",
  })
  .refine(
    (valueLinks) => {
      return checkUserOrder(valueLinks);
    },
    { message: "User order values must be unique" }
  );

export const moralProfileReadSchema = z
  .object({
    initial: z.boolean(),
    attitudes: z.array(attitudeReadSchema),
    value_links: valuesArray,
  })
  .describe("moralProfileReadSchema");

export const moralProfileSubmitSchema = z
  .object({
    attitude_id: z.number().int().positive({
      message: "Attitude ID must be a positive integer",
    }),
    value_links: valuesSubmitArray,
  })
  .describe("submitMoralProfile");

export const moralProfileResponseSchema = z
  .object({
    data: moralProfileReadSchema,
    message: z.string(),
  })
  .describe("myValuesResponseSchema");
