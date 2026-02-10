import * as sch from "@/src/schemas";
import { validateSchema } from "@/src/utils";
import { API_CFG } from "@/src/config";
import { verifyDataAfterSubmit } from "@/src/utils";
import { apiClient } from "./client";
import * as typ from "@/src/types/api";

export async function getProfile(): Promise<typ.ProfileResponse> {
  const response = await apiClient.get<typ.ProfileResponse>(
    API_CFG.PRIVATE.PROFILE,
  );
  validateSchema<typ.ProfileResponse>(sch.profileResponseSchema, response.data);
  return response.data as typ.ProfileResponse;
}

export async function submitProfile(
  data: typ.ProfileWrite,
): Promise<typ.ProfileResponse> {
  validateSchema<typ.ProfileWrite>(sch.profileWriteSchema, data);
  const response = await apiClient.put<typ.ProfileResponse>(
    API_CFG.PRIVATE.PROFILE,
    data,
  );
  validateSchema<typ.ProfileResponse>(sch.profileResponseSchema, response.data);
  verifyDataAfterSubmit(data, response.data.data);
  return response.data as typ.ProfileResponse;
}
