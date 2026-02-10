import * as sch from "@/src/schemas";
import { validateSchema } from "@/src/utils";
import { API_CFG } from "@/src/config";
import { apiClient } from "./client";
import * as typ from "@/src/types/api";

async function _contactAction(
  userId: string,
  endpoint: string,
): Promise<typ.ContactsAndRequestsResponse> {
  validateSchema<string>(sch.uuidSchema, userId);
  const response = await apiClient.post<typ.ContactsAndRequestsResponse>(
    endpoint,
    { id: userId },
  );
  validateSchema<typ.ContactsAndRequestsResponse>(
    sch.contactsAndRequestsResponseSchema,
    response.data,
  );
  return response.data as typ.ContactsAndRequestsResponse;
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

export async function getContactProfile(
  contactId: string,
): Promise<typ.OtherProfileResponse> {
  validateSchema<string>(sch.uuidSchema, contactId);
  const response = await apiClient.get<typ.OtherProfileResponse>(
    `${API_CFG.PRIVATE.CONTACT_PROFILE}/${contactId}`,
  );
  validateSchema<typ.OtherProfileResponse>(
    sch.otherProfileResponseSchema,
    response.data,
  );
  return response.data as typ.OtherProfileResponse;
}

export async function agreeToStart(
  userId: string,
): Promise<typ.ContactsAndRequestsResponse> {
  return _contactAction(userId, API_CFG.PRIVATE.AGREE_TO_START);
}

export async function cancelContactRequest(
  userId: string,
): Promise<typ.ContactsAndRequestsResponse> {
  return _contactAction(userId, API_CFG.PRIVATE.CANCEL_REQUEST);
}

export async function rejectContactRequest(
  userId: string,
): Promise<typ.ContactsAndRequestsResponse> {
  return _contactAction(userId, API_CFG.PRIVATE.REJECT_REQUEST);
}

export async function blockContact(
  userId: string,
): Promise<typ.ContactsAndRequestsResponse> {
  return _contactAction(userId, API_CFG.PRIVATE.BLOCK_USER);
}

export async function unblockContact(
  userId: string,
): Promise<typ.ContactsAndRequestsResponse> {
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
