import { API_CFG } from "@/src/config";
import * as sch from "@/src/schemas";
import * as typ from "@/src/types/api";
import { validateSchema, verifyDataAfterSubmit } from "@/src/utils";
import { apiClient } from "./client";

export async function getMessages(
  contactId: string,
): Promise<typ.MessagesGetResponse> {
  validateSchema<string>(sch.uuidSchema, contactId);
  const response = await apiClient.get<typ.MessagesGetResponse>(
    `${API_CFG.PRIVATE.MESSAGES}/?contact_user_id=${contactId}`,
  );
  validateSchema<typ.MessagesGetResponse>(
    sch.messagesGetResponseSchema,
    response.data,
  );
  return response.data as typ.MessagesGetResponse;
}
export async function postMessage(
  data: typ.MessageWrite,
): Promise<typ.MessagePostResponse> {
  validateSchema<typ.MessageWrite>(sch.messageWriteSchema, data);
  const response = await apiClient.post<typ.MessagePostResponse>(
    API_CFG.PRIVATE.MESSAGES,
    data,
  );
  validateSchema<typ.MessagePostResponse>(
    sch.messagePostResponseSchema,
    response.data,
  );
  verifyDataAfterSubmit(data, response.data.data, ["receiver_id", "text"]);
  return response.data as typ.MessagePostResponse;
}
