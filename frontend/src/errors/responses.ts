import { AppError } from "./common";

export class DataMismatch extends AppError {
  constructor(
    params: {
      message?: string;
      originalError?: Error;
    } = {}
  ) {
    const { message = "Data mismatch.", originalError } = params;

    super({
      message,
      code: "DATA_MISMATCH",
      originalError,
    });

    this.name = "DataMismatch";
  }
}
