/** Consistent error envelope returned by every /api/v1/* endpoint on failure. */
export interface ApiErrorBody {
  error: {
    code: string;
    message: string;
    requestId: string;
  };
}

export class ApiError extends Error {
  readonly code: string;
  readonly requestId: string;

  constructor(body: ApiErrorBody) {
    super(body.error.message);
    this.name = "ApiError";
    this.code = body.error.code;
    this.requestId = body.error.requestId;
  }
}
