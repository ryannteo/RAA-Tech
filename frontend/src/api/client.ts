import type { DisputeResult } from "../types";

const BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000";

export interface SubmitDisputePayload {
  category: string;
  trip_id: string;
  rider_id: string;
  driver_id: string;
  rider_statement: string;
  driver_statement?: string;
}

export async function submitDispute(payload: SubmitDisputePayload): Promise<DisputeResult> {
  const res = await fetch(`${BASE_URL}/disputes`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!res.ok) throw new Error(`Failed to submit dispute: ${res.status}`);
  return res.json();
}

export async function listDisputes(): Promise<DisputeResult[]> {
  const res = await fetch(`${BASE_URL}/disputes`);
  if (!res.ok) throw new Error(`Failed to list disputes: ${res.status}`);
  return res.json();
}
