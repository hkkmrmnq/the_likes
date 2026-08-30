import * as sch from "@/src/schemas";
import { validateSchema } from "@/src/utils";
import { API_CFG } from "@/src/config";
import { apiClient } from "./client";
import * as typ from "@/src/types/api";
import { DataMismatch } from "@/src/errors";

async function _contactAction(
  userId: string,
  endpoint: string,
): Promise<typ.ContsNReqstsNRecomsSchemaResponse> {
  validateSchema<string>(sch.uuidSchema, userId);
  const response = await apiClient.post<typ.ContsNReqstsNRecomsSchemaResponse>(
    endpoint,
    { id: userId },
  );
  validateSchema<typ.ContsNReqstsNRecomsSchemaResponse>(
    sch.contsNReqstsNRecomsSchemaResponseSchema,
    response.data,
  );
  return response.data as typ.ContsNReqstsNRecomsSchemaResponse;
}

export async function getContsNReqstsNRecoms(): Promise<typ.ContsNReqstsNRecomsSchemaResponse> {
  const response = await apiClient.get<typ.ContsNReqstsNRecomsSchemaResponse>(
    API_CFG.PRIVATE.CONTS_N_REQSTS_RECOMS,
  );
  validateSchema<typ.ContsNReqstsNRecomsSchemaResponse>(
    sch.contsNReqstsNRecomsSchemaResponseSchema,
    response.data,
  );
  return response.data as typ.ContsNReqstsNRecomsSchemaResponse;
}

export async function agreeToStart(
  userId: string,
): Promise<typ.ContsNReqstsNRecomsSchemaResponse> {
  return _contactAction(userId, API_CFG.PRIVATE.AGREE_TO_START);
}

export async function cancelContactRequest(
  userId: string,
): Promise<typ.ContsNReqstsNRecomsSchemaResponse> {
  return _contactAction(userId, API_CFG.PRIVATE.CANCEL_REQUEST);
}

export async function rejectContactRequest(
  userId: string,
): Promise<typ.ContsNReqstsNRecomsSchemaResponse> {
  return _contactAction(userId, API_CFG.PRIVATE.REJECT_REQUEST);
}

export async function blockContact(
  userId: string,
): Promise<typ.ContsNReqstsNRecomsSchemaResponse> {
  return _contactAction(userId, API_CFG.PRIVATE.BLOCK_USER);
}

export async function unblockContact(
  userId: string,
): Promise<typ.ContsNReqstsNRecomsSchemaResponse> {
  return _contactAction(userId, API_CFG.PRIVATE.UNBLOCK_USER);
}

export async function getContactsOptions(): Promise<typ.ContactsOptionsResponse> {
  const response = await apiClient.get<typ.ContactsOptionsResponse>(
    API_CFG.PRIVATE.CONTACTS_OPTIONS,
  );
  validateSchema<typ.ContactsOptionsResponse>(
    sch.contactsOptionsResponseSchema,
    response.data,
  );
  return response.data as typ.ContactsOptionsResponse;
}

export async function updateContactAlias(
  userId: string,
  newAlias: string,
): Promise<typ.Contact> {
  validateSchema<string>(sch.uuidSchema, userId);
  validateSchema<string | null>(sch.nameSchema, newAlias);
  const response = await apiClient.post<typ.UpdateContactAliasResponseSchema>(
    API_CFG.PRIVATE.UPDATE_ALIAS,
    { user_id: userId, new_alias: newAlias },
  );
  validateSchema<typ.UpdateContactAliasResponseSchema>(
    sch.updateContactAliasResponseSchema,
    response.data,
  );
  const updated = response.data.data;
  if (updated.user_id !== userId || updated.alias !== newAlias) {
    throw new DataMismatch({
      message: `sent {userId: ${userId}, alias: ${newAlias}}, received: ${updated}`,
    });
  }
  return updated as typ.Contact;
}
