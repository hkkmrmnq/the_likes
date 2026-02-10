import { AppError } from "./common";

export class BadRequestError extends AppError {
  constructor(
    params: {
      message?: string;
      originalError?: Error;
    } = {}
  ) {
    const { message = "Bad Request.", originalError } = params;

    super({
      message,
      code: "BAD_REQUEST",
      originalError,
    });

    this.name = "BadRequestError";
  }
}

export class Unauthorized extends AppError {
  constructor(
    params: {
      message?: string;
      originalError?: Error;
    } = {}
  ) {
    const { message = "Unauthorized.", originalError } = params;

    super({
      message,
      code: "UNAUTHORIZED",
      originalError,
    });

    this.name = "Unauthorized";
  }
}

export class ServerError extends AppError {
  constructor(
    params: {
      message?: string;
      originalError?: Error;
    } = {}
  ) {
    const { message = "Unexpected backend error", originalError } = params;

    super({
      message,
      code: "BACKEND_ERROR",
      originalError,
    });

    this.name = "BackendServerError";
  }
}

export class ForbiddenError extends AppError {
  constructor(
    params: {
      message?: string;
      originalError?: Error;
    } = {}
  ) {
    const { message = "Access denied", originalError } = params;

    super({
      message,
      code: "FORBIDDEN",
      originalError,
    });

    this.name = "ForbiddenError";
  }
}
