import type { AdvocateFailureDetail, DisputeResult, ScenarioSummary, SubmitDisputePayload } from "../types";
export type { SubmitDisputePayload } from "../types";

const BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000";

async function readResponse<T>(res: Response): Promise<T> {
  if (!res.ok) {
    const body: unknown = await res.json().catch(() => null);
    const detail = body && typeof body === "object" && "detail" in body ? body.detail : null;
    const structured = detail as Partial<AdvocateFailureDetail> | null;
    const message = typeof detail === "string"
      ? detail
      : structured && typeof structured.message === "string"
        ? structured.message
        : `Request failed (${res.status})`;
    throw new Error(message);
  }
  return res.json();
}

export async function listScenarios(): Promise<ScenarioSummary[]> {
  return readResponse<ScenarioSummary[]>(await fetch(`${BASE_URL}/disputes/scenarios`));
}

export async function submitDispute(payload: SubmitDisputePayload): Promise<DisputeResult> {
  return readResponse<DisputeResult>(await fetch(`${BASE_URL}/disputes`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  }));
}

export async function listDisputes(): Promise<DisputeResult[]> {
  return readResponse<DisputeResult[]>(await fetch(`${BASE_URL}/disputes`));
}
