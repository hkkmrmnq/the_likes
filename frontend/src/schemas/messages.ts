import { z } from "zod";

import {
  uuidSchema,
  dataTimeShchema,
  messageTextSchema,
  timeSchema,
} from "./base";

const messageShapeBase = {
  receiver_id: uuidSchema,
  text: messageTextSchema,
};

export const messageReadSchema = z
  .object({
    ...messageShapeBase,
    sender_id: uuidSchema,
    sender_name: z.string().nullable(),
    receiver_name: z.string().nullable(),
    created_at: dataTimeShchema,
    time: timeSchema,
  })
  .describe("messageReadSchema");

// export const messagesReadSchema = z.array(messageReadSchema);

export const messagesGetResponseSchema = z.object({
  data: z.array(messageReadSchema),
  message: messageTextSchema,
});

export const messageWriteSchema = z
  .object(messageShapeBase)
  .describe("messageWriteSchema");

export const messagePostResponseSchema = z.object({
  data: messageReadSchema,
  message: messageTextSchema,
});
