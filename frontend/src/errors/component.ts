import { AppError } from "./common";

export class ComponentError extends AppError {
  constructor(
    params: {
      message?: string;
      originalError?: Error;
    } = {}
  ) {
    const { message = "Component error.", originalError } = params;

    super({
      message,
      code: "COMPONENT_ERROR",
      originalError,
    });

    this.name = "ComponentError";
  }
}
