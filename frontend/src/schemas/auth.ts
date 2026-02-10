import { z } from "zod";

export const accessTokenSchema = z
  .object({
    access_token: z.string(),
    token_type: z.string(),
  })
  .describe("accessTokenSchema");

export const loginResponseSchema = z
  .object({
    data: accessTokenSchema,
    message: z.string(),
  })
  .describe("loginResponseSchema");

const passwordSchema = z
  .string()
  .min(8, "Password must be at least 8 characters")
  .max(128, "Password must be less than 128 characters")
  .refine(
    (value) => /[a-z]/.test(value),
    "Password must contain at least one lowercase letter",
  )
  .refine(
    (value) => /[A-Z]/.test(value),
    "Password must contain at least one uppercase letter",
  )
  .refine(
    (value) => /\d/.test(value),
    "Password must contain at least one number",
  )
  .refine(
    (value) => /[^a-zA-Z0-9]/.test(value),
    "Password must contain at least one special character (e.g., !@#$%)",
  );

const confirmationCodeSchema = z
  .string()
  .length(6, "6 digits string expected")
  .refine((val) => /^\d+$/.test(val), {
    message: "Should contain only digits",
  });

export const registerSchema = z.object({
  email: z.email(),
  password: passwordSchema,
});

export const registerResponseSchema = z.object({
  data: z.string(),
  message: z.string(),
});

export const verifyEmailSchema = z.object({
  email: z.email(),
  code: confirmationCodeSchema,
});

export const verifyEmailResponseSchema = z.object({
  data: z.null(),
  message: z.string(),
});

export const loginSchema = z.object({
  email: z.email(),
  password: z.string().min(1, "Password is required"),
});

export const forgotPasswordSchema = z.object({
  email: z.email(),
});

export const forgotPasswordResponseSchema = z.object({
  data: z.null(),
  message: z.string(),
});

export const setNewPasswordSchema = z.object({
  email: z.email(),
  password: z.string().min(1, "Password is required"),
  code: confirmationCodeSchema,
});

export const setNewPasswordResponseSchema = z.object({
  message: z.string(),
});
