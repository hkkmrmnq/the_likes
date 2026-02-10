export class AppError extends Error {
  public code: string;
  public originalError?: Error;

  constructor(params: {
    message: string;
    code: string;
    originalError?: Error;
  }) {
    super(params.message);
    this.name = "AppError";
    this.code = params.code;
    this.originalError = params.originalError;
  }
}

export class ValidationError extends AppError {
  errors: Record<string, string>;

  constructor(params: {
    errors: Record<string, string>;
    message?: string;
    originalError?: Error;
  }) {
    const { errors, message = "Validation failed", originalError } = params;

    super({
      message,
      code: "VALIDATION_ERROR",
      originalError,
    });

    this.name = "ValidationError";
    this.errors = errors;
  }
}
