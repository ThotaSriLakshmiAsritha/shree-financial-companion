import type {
  AuthMeResponse,
  HealthResponse,
  ProfileUpdateRequest,
} from "@sahachari/contracts";

const API_BASE_URL = (import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000").replace(/\/$/, "");

export class ApiError extends Error {
  constructor(
    message: string,
    public readonly status: number,
    public readonly code = "api_error",
  ) {
    super(message);
    this.name = "ApiError";
  }
}

async function request<T>(path: string, init?: RequestInit, accessToken?: string): Promise<T> {
  let response: Response;

  try {
    response = await fetch(`${API_BASE_URL}${path}`, {
      ...init,
      headers: {
        Accept: "application/json",
        ...(accessToken ? { Authorization: `Bearer ${accessToken}` } : {}),
        ...init?.headers,
      },
    });
  } catch {
    throw new ApiError("Unable to reach the Sahachari API.", 0, "network_error");
  }

  if (!response.ok) {
    let message = "The API request failed.";
    try {
      const body = (await response.json()) as { error?: { message?: string } };
      message = body.error?.message ?? message;
    } catch {
      // Keep the stable fallback message when the response is not JSON.
    }
    throw new ApiError(message, response.status);
  }

  return (await response.json()) as T;
}

export function getHealth(): Promise<HealthResponse> {
  return request<HealthResponse>("/health");
}

export function getAuthMe(accessToken: string): Promise<AuthMeResponse> {
  return request<AuthMeResponse>("/auth/me", undefined, accessToken);
}

export function updateAuthMe(accessToken: string, payload: ProfileUpdateRequest): Promise<AuthMeResponse> {
  return request<AuthMeResponse>(
    "/auth/me",
    {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    },
    accessToken,
  );
}
