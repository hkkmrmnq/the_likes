import { toast } from "sonner";
import { API_CFG } from "@/src/config";
import { apiClient } from "./client";
import {
  moralProfileResponseSchema,
  moralProfileSubmitSchema,
} from "@/src/schemas";
import { MoralProfileResponse, MoralProfileSubmit } from "@/src/types/api";
import { validateSchema } from "@/src/utils";

export async function getValues(): Promise<MoralProfileResponse> {
  const response = await apiClient.get<MoralProfileResponse>(
    API_CFG.PRIVATE.VALUES,
  );
  validateSchema<MoralProfileResponse>(
    moralProfileResponseSchema,
    response.data,
  );
  // toast.info(response.data.message);
  return response.data as MoralProfileResponse;
}
export async function submitValues(
  initial: boolean,
  data: MoralProfileSubmit,
): Promise<MoralProfileResponse> {
  const call = initial
    ? apiClient.post<MoralProfileResponse>
    : apiClient.put<MoralProfileResponse>;

  validateSchema<MoralProfileSubmit>(moralProfileSubmitSchema, data);
  const response = await call(API_CFG.PRIVATE.VALUES, data);
  validateSchema<MoralProfileResponse>(
    moralProfileResponseSchema,
    response.data,
  );
  toast.info(response.data.message);
  return response.data as MoralProfileResponse;
}
