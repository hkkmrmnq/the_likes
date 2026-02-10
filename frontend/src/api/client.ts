import axios, { AxiosError } from "axios";
import { toast } from "sonner";
import { API_CFG } from "@/src/config";
import { authStore } from "@/src/stores/auth";
import { ErrorResponse, BackendValidationErrorDetail } from "@/src/types/api";
import * as exc from "@/src/errors";

export const apiClient = axios.create({
  baseURL: API_CFG.BASE_URL_REST,
  timeout: API_CFG.TIMEOUT,
  headers: {
    "Content-Type": "application/json",
  },
});

function handleGeneralApiError(error: AxiosError) {
  if (!error.response) {
    console.error("No response.");
    throw new exc.AppError({
      message: "Network error",
      code: "NETWORK_ERROR",
      originalError: error,
    });
  }
  const errorData = error.response.data as ErrorResponse;
  let message =
    typeof errorData?.detail === "string"
      ? errorData.detail
      : `Error ${error.response.status}`;
  switch (error.response.status) {
    case 400:
      switch (message) {
        case "LOGIN_BAD_CREDENTIALS":
          message = "Incorrect email or password.";
          break;
        case "REGISTER_USER_ALREADY_EXISTS":
          message = "User with this email already registered.";
      }
      toast.error("Bad request.");
      throw new exc.BadRequestError({
        message,
        originalError: error,
      });
    case 401:
      const { clearCreds } = authStore.getState();
      clearCreds();
      toast.error(message || "Authorization required.");
      throw new exc.Unauthorized({
        message,
        originalError: error,
      });
    case 403:
      toast.error(message || "Access denied.");
      throw new exc.ForbiddenError({
        message,
        originalError: error,
      });
    case 422:
      toast.error("Data validation error.");
      let errors: Record<string, string> = {};
      if (Array.isArray(errorData?.detail)) {
        const details = errorData.detail as BackendValidationErrorDetail[];
        details.forEach((detail) => {
          const field = detail.loc[1];
          if (typeof field === "string") {
            errors[field] = detail.msg;
          }
        });
      } else {
        errors = { form: "Validation failed" };
      }
      throw new exc.ValidationError({
        errors,
        originalError: error,
      });
    case 500:
      toast.error("Unexpected server error.");
      throw new exc.ServerError({
        message,
        originalError: error,
      });
    default:
      toast.error(message);
      throw new exc.AppError({
        message,
        code: `HTTP_${error.response.status}`,
        originalError: error,
      });
  }
}

apiClient.interceptors.request.use((config) => {
  if (config.headers === undefined) {
    throw Error("Request interceptor: undefined config.headers.");
  }
  if (config.url === undefined) {
    throw Error("Request interceptor: undefined config.url.");
  }
  const publicApiPath = !(Object.values(API_CFG.PUBLIC) as string[]).includes(
    config.url,
  );
  if (publicApiPath) {
    const { token, expiresAt } = authStore.getState();
    if (!token || expiresAt < Date.now()) {
      toast.info("Authentication required.");
      throw new exc.AppError({
        message: "Authentication required.",
        code: "AUTH_ERROR",
      });
    }
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (axios.isCancel(error)) {
      throw error;
    }
    handleGeneralApiError(error);
  },
);
