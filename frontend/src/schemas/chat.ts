import { z } from "zod";

import { uuidSchema, dataTimeShchema, timeSchema } from "./base";
import { contactRichSchema, otherProfileSchema } from "./contacts";
import { messageWriteSchema, messageReadSchema } from "./messages";

export enum ChatPayloadType {
  CREATE_MSG = "CREATE_MSG",
  NEW_MSG = "NEW_MSG",
  MSG_SENT = "MSG_SENT",
  MSG_ERROR = "MSG_ERROR",
  PING = "PING",
  PONG = "PONG",
  NEW_RECOMM = "NEW_RECOMM",
  NEW_REQUEST = "NEW_REQUEST",
  NEW_CHAT = "NEW_CHAT",
  BLOCKED_BY = "BLOCKED_BY",
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

export const beatSchema = z.object({
  origin: z.enum(["BACK", "FRONT"]),
});

export const chatPayloadSchema = z.discriminatedUnion("payload_type", [
  z.object({
    payload_type: z.literal(ChatPayloadType.CREATE_MSG),
    related_content: messageWriteSchema,
    timestamp: dataTimeShchema,
  }),
  z.object({
    payload_type: z.literal(ChatPayloadType.NEW_MSG),
    related_content: messageReadSchema,
    timestamp: dataTimeShchema,
  }),
  z.object({
    payload_type: z.literal(ChatPayloadType.PING),
    related_content: beatSchema,
    timestamp: dataTimeShchema,
  }),
  z.object({
    payload_type: z.literal(ChatPayloadType.PONG),
    related_content: beatSchema,
    timestamp: dataTimeShchema,
  }),
  z.object({
    payload_type: z.literal(ChatPayloadType.MSG_SENT),
    related_content: messageSentSchema,
    timestamp: dataTimeShchema,
  }),
  z.object({
    payload_type: z.literal(ChatPayloadType.MSG_ERROR),
    related_content: messageErrorSchema,
    timestamp: dataTimeShchema,
  }),
  z.object({
    payload_type: z.literal(ChatPayloadType.NEW_RECOMM),
    related_content: otherProfileSchema,
    timestamp: dataTimeShchema,
  }),
  z.object({
    payload_type: z.literal(ChatPayloadType.NEW_REQUEST),
    related_content: contactRichSchema,
    timestamp: dataTimeShchema,
  }),
  z.object({
    payload_type: z.literal(ChatPayloadType.NEW_CHAT),
    related_content: contactRichSchema,
    timestamp: dataTimeShchema,
  }),
  z.object({
    payload_type: z.literal(ChatPayloadType.BLOCKED_BY),
    related_content: contactRichSchema,
    timestamp: dataTimeShchema,
  }),
]);
