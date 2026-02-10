import { z } from "zod";
import * as sch from "@/src/schemas";
export { ChatPayloadType } from "@/src/schemas";

export type RegisterInput = z.infer<typeof sch.registerSchema>;
export type RegisterResponse = z.infer<typeof sch.registerResponseSchema>;
export type VerifyEmail = z.infer<typeof sch.verifyEmailSchema>;
export type VerifyEmailResponse = z.infer<typeof sch.verifyEmailResponseSchema>;
export type SetNewPassword = z.infer<typeof sch.setNewPasswordSchema>;
export type SetNewPasswordResponse = z.infer<
  typeof sch.setNewPasswordResponseSchema
>;
export type LoginInput = z.infer<typeof sch.loginSchema>;
export type ForgotPassword = z.infer<typeof sch.forgotPasswordSchema>;
export type ForgotPasswordResponse = z.infer<
  typeof sch.forgotPasswordResponseSchema
>;
export type LoginResponse = z.infer<typeof sch.loginResponseSchema>;
export type Languages = z.infer<typeof sch.languagesSchema>;
export type ProfileRead = z.infer<typeof sch.profileReadSchema>;
export type ProfileWrite = z.infer<typeof sch.profileWriteSchema>;
export type ProfileResponse = z.infer<typeof sch.profileResponseSchema>;
export type Attitude = z.infer<typeof sch.attitudeReadSchema>;
export type ValueLinks = z.infer<typeof sch.valuesArray>;
export type ValueLinksToSubmit = z.infer<typeof sch.valuesSubmitArray>;
export type MoralProfileRead = z.infer<typeof sch.moralProfileReadSchema>;
export type MoralProfileSubmit = z.infer<typeof sch.moralProfileSubmitSchema>;
export type MoralProfileResponse = z.infer<
  typeof sch.moralProfileResponseSchema
>;
export type MessageRead = z.infer<typeof sch.messageReadSchema>;
export type MessagesGetResponse = z.infer<typeof sch.messagesGetResponseSchema>;
export type MessageWrite = z.infer<typeof sch.messageWriteSchema>;
export type MessagePostResponse = z.infer<typeof sch.messagePostResponseSchema>;
export type OtherProfile = z.infer<typeof sch.otherProfileSchema>;
export type OtherProfileResponse = z.infer<
  typeof sch.otherProfileResponseSchema
>;
export type Recommendation = z.infer<typeof sch.recommendationSchema>;
export type ContactRequest = z.infer<typeof sch.contactRequestSchema>;
export type Contact = z.infer<typeof sch.contactSchema>;
export type ContactRich = z.infer<typeof sch.contactRichSchema>;
export type ContactsAndRequestsResponse = z.infer<
  typeof sch.contactsAndRequestsResponseSchema
>;
export type ContsNReqstsNRecomsSchemaResponse = z.infer<
  typeof sch.contsNReqstsNRecomsSchemaResponseSchema
>;

export type ContactsOptions = z.infer<typeof sch.contactsOptionsSchema>;

export type ContactsOptionsResponse = z.infer<
  typeof sch.contactsOptionsResponseSchema
>;

export interface ErrorResponse {
  detail: string | BackendValidationErrorDetail[];
  [key: string]: unknown;
}

export interface ProfileDataFromComponent {
  name: string;
  languages: Array<string>;
  longitude: string;
  latitude: string;
  distance_limit: string;
  recommend_me: boolean;
}

export type Polarity = "positive" | "negative" | "neutral";

export type ValidationSuccess<T> = { success: true; data: T };
export type ValidationFailure = {
  success: false;
  errors: Record<string, string>;
};
export interface BackendValidationErrorDetail {
  type: string;
  loc: Array<string>;
  msg: string;
  input: string | number;
  ctx?: object;
}

export interface WebSocketConfig {
  url: string;
  token: string;
  autoReconnect?: boolean;
  maxReconnectAttempts?: number;
  reconnectDelay?: number;
}

export type MeessageError = z.infer<typeof sch.messageErrorSchema>;
export type ChatPayload = z.infer<typeof sch.chatPayloadSchema>;
export type MessageSent = z.infer<typeof sch.messageSentSchema>;
export type TargetUser = z.infer<typeof sch.targetUserSchema>;
