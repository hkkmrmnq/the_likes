import { z } from "zod";

import { uuidSchema, dataTimeShchema, timeSchema } from "./base";
import { messageWriteSchema, messageReadSchema } from "./messages";

export enum ChatPayloadType {
  CREATE = "CREATE",
  NEW = "NEW",
  SENT = "SENT",
  ERROR = "ERROR",
  PING = "PING",
  PONG = "PONG",
}

export const messageSentSchema = z
  .object({
    receiver_id: uuidSchema,
    client_id: uuidSchema,
    created_at: dataTimeShchema,
    time: timeSchema,
  })
  .describe("messageSentSchema");

export const messageErrorSchema = z
  .object({
    error: z.string(),
  })
  .describe("messageErrorSchema");

export const targetUserSchema = z.object({
  user_id: uuidSchema,
});

export const pingPongSchema = z.object({
  ping_timestamp: z.string().datetime().nullable(), // only use for pong
});

export const chatPayloadSchema = z.discriminatedUnion("payload_type", [
  z.object({
    payload_type: z.literal(ChatPayloadType.CREATE),
    related_content: messageWriteSchema,
    timestamp: z.string().datetime(),
  }),
  z.object({
    payload_type: z.literal(ChatPayloadType.NEW),
    related_content: messageReadSchema,
    timestamp: z.string().datetime(),
  }),
  z.object({
    payload_type: z.literal(ChatPayloadType.PING),
    related_content: pingPongSchema,
    timestamp: z.string().datetime(),
  }),
  z.object({
    payload_type: z.literal(ChatPayloadType.PONG),
    related_content: pingPongSchema,
    timestamp: z.string().datetime(),
  }),
  z.object({
    payload_type: z.literal(ChatPayloadType.SENT),
    related_content: messageSentSchema,
    timestamp: z.string().datetime(),
  }),
  z.object({
    payload_type: z.literal(ChatPayloadType.ERROR),
    related_content: messageErrorSchema,
    timestamp: z.string().datetime(),
  }),
]);
