import { z } from "zod";
import { ValidationError } from "@/src/errors";
import * as exc from "@/src/errors";

export function validateSchema<T>(schema: z.ZodSchema<T>, data: unknown) {
  const result = schema.safeParse(data);

  if (!!result.success) return;

  const errors: Record<string, string> = {};

  result.error.issues.forEach((issue) => {
    const path = issue.path.join(".");
    errors[path || "_form"] = issue.message;
  });

  throw new exc.ValidationError({
    errors,
    message: `${schema.description} validation erro(s).`,
  });
}

export function handleErrorInComponent(
  error: unknown,
  setError: (msg: string) => void,
  setFieldErrors?: (fieldErrors: Record<string, string>) => void,
) {
  let msg = `Error: ${error}`;
  if (error instanceof ValidationError) {
    if (!!setFieldErrors) {
      setFieldErrors(error.errors);
    }
    msg = error.message;
    console.error(msg);
    console.error(error.errors);
  } else if (error instanceof Error) {
    msg = error.message;
    console.error(msg);
    setError(msg);
  } else {
    console.error(msg);
    setError(msg);
  }
}

type T1 = Record<string, unknown>;
type T2 = Record<string, unknown>;
export function verifyDataAfterSubmit(
  sent: T1,
  received: T2,
  fieldsToVerify: (keyof T1)[] | (keyof T2)[] | null = null,
): void {
  if (fieldsToVerify === null) {
    fieldsToVerify = Object.keys(sent);
  }
  const dataIsEqual = fieldsToVerify.every((field) => {
    const sentVal = sent[field];
    const recvVal = received[field];

    const fieldIsEqual =
      typeof sentVal === "object" || Array.isArray(sentVal)
        ? JSON.stringify(sentVal) === JSON.stringify(recvVal)
        : sentVal === recvVal;

    if (!fieldIsEqual) {
      console.warn(`Field ${String(field)} mismatch:`, {
        sent: sentVal,
        received: recvVal,
      });
    }
    return fieldIsEqual;
  });
  if (!dataIsEqual) {
    throw new exc.DataMismatch({
      message: "Response data does not match submitted.",
    });
  }
}

export const truncate = (str: string, limit: number) => {
  return str.length > limit ? `${str.slice(0, limit)}...` : str;
};
