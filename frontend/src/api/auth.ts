import { apiClient } from "./client";
import { API_CFG } from "@/src/config";
import * as typ from "@/src/types";
import * as sch from "@/src/schemas";
import { validateSchema } from "@/src/utils";
import * as exc from "@/src/errors";

function checkIfPasswordsAreSame(password: string, confirmPassword: string) {
  if (password !== confirmPassword) {
    throw new exc.ValidationError({
      errors: {
        password: "Passwords don't match",
        confirmPassword: "Passwords don't match",
      },
    });
  }
}

export async function login(credentials: { email: string; password: string }) {
  validateSchema<typ.LoginInput>(sch.loginSchema, credentials);
  const response = await apiClient.post(API_CFG.PUBLIC.LOGIN, credentials);
  validateSchema<typ.LoginResponse>(sch.loginResponseSchema, response.data);
  return response.data.data.access_token as string;
}

export async function register(
  email: string,
  password: string,
  confirmPassword: string,
): Promise<typ.RegisterResponse> {
  checkIfPasswordsAreSame(password, confirmPassword);
  const payload = { email, password };
  validateSchema<typ.RegisterInput>(sch.registerSchema, payload);
  const response = await apiClient.post(API_CFG.PUBLIC.REGISTER, payload);
  validateSchema<typ.RegisterResponse>(
    sch.registerResponseSchema,
    response.data,
  );
  return response.data as typ.RegisterResponse;
}

export async function verifyEmail(email: string, code: string) {
  const payload = { email, code };
  validateSchema<typ.VerifyEmail>(sch.verifyEmailSchema, payload);
  const response = await apiClient.post(API_CFG.PUBLIC.VERIFY, payload);
  validateSchema<typ.VerifyEmailResponse>(
    sch.verifyEmailResponseSchema,
    response.data,
  );
  return response.data as typ.VerifyEmailResponse;
}

export async function forgotPassword(data: { email: string }) {
  validateSchema<typ.ForgotPassword>(sch.forgotPasswordSchema, data);
  const response = await apiClient.post(API_CFG.PUBLIC.FORGOT_PASSWORD, data);
  validateSchema<typ.ForgotPasswordResponse>(
    sch.forgotPasswordResponseSchema,
    response.data,
  );
  return response.data.message as string;
}

export async function setNewPassword(
  email: string,
  password: string,
  confirmPassword: string,
  code: string,
) {
  const payload = { email, password, code };
  checkIfPasswordsAreSame(password, confirmPassword);
  validateSchema<typ.SetNewPassword>(sch.setNewPasswordSchema, payload);
  const response = await apiClient.post(
    API_CFG.PUBLIC.SET_NEW_PASSWORD,
    payload,
  );
  validateSchema<typ.SetNewPasswordResponse>(
    sch.setNewPasswordResponseSchema,
    response.data,
  );
  return response.data.message as typ.SetNewPasswordResponse;
}
