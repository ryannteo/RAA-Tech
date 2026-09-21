// Public API contract: backend/app/schemas/dispute.py.
export type DisputeCategory = "route_deviation" | "no_show";
export type ScenarioId = "route_deviation_001" | "no_show_001";
export type ResolutionStatus = "resolved" | "needs_review";
export type AgentSource = "stub" | "llm";
export type Decision = "full_refund" | "partial_refund" | "no_action";

export interface SubmitDisputePayload {
  scenario_id: ScenarioId;
  category: DisputeCategory;
  rider_statement?: string | null;
  driver_statement?: string | null;
}

export interface Dispute {
  dispute_id: string;
  scenario_id: ScenarioId;
  category: DisputeCategory;
  trip_id: string;
  rider_id: string;
  driver_id: string;
  rider_statement: string | null;
  driver_statement: string | null;
}

export interface ScenarioSummary {
  scenario_id: ScenarioId;
  category: DisputeCategory;
  title: string;
  description: string;
}

export type EvidenceItem<T> =
  | { availability: "available"; data: T; reason: null }
  | { availability: "unavailable"; data: null; reason: string };

export interface GPSPoint {
  timestamp: string;
  latitude: number;
  longitude: number;
  accuracy_m: number;
}

export interface GPSTelemetry {
  points: GPSPoint[];
  actual_route_km: number | null;
  estimated_route_km: number | null;
  waiting_minutes: number | null;
  pickup_distance_m: number | null;
  events: { timestamp: string; source: string; description: string }[];
  limitations: string[];
}

export interface ChatMessage {
  timestamp: string;
  sender: "rider" | "driver" | "system";
  message: string;
  delivered: boolean | null;
}

export interface FareData {
  currency: "SGD";
  quoted_total: number | null;
  charged_total: number | null;
  distance_charge: number | null;
  cancellation_fee: number | null;
  tolls: number | null;
  limitations: string[];
}

export interface AccountHistory {
  completed_trips: number | null;
  prior_disputes: number | null;
  prior_cancellations: number | null;
}

export interface UserHistory {
  rider: AccountHistory;
  driver: AccountHistory;
  limitations: string[];
}

export interface EvidenceBundle {
  scenario_id: ScenarioId;
  trip_id: string;
  gps_data: EvidenceItem<GPSTelemetry>;
  chat_logs: EvidenceItem<ChatMessage[]>;
  fare_data: EvidenceItem<FareData>;
  user_history: EvidenceItem<UserHistory>;
}

export interface PolicyContext {
  category: DisputeCategory;
  version: string;
  is_mock: boolean;
  rules: { rule_id: string; title: string; text: string }[];
}

export interface AdvocateCase {
  side: "rider" | "driver";
  claim: string;
  supporting_points: string[];
  requested_outcome: Decision | "undetermined";
  source: AgentSource;
}

export interface AdvocateFailureDetail {
  code: "advocate_contract_failure";
  stage: "rider_advocate" | "driver_advocate";
  message: string;
}

export interface Ruling {
  decision: Decision;
  amount: number | null;
  currency: "SGD";
  reasoning: string;
  confidence: number;
  source: AgentSource;
}

export interface AgentLogEntry {
  agent: string;
  message: string;
  timestamp: string;
}

export interface DisputeResult {
  dispute: Dispute;
  priority: "normal";
  evidence: EvidenceBundle;
  policy: PolicyContext;
  rider_case: AdvocateCase;
  driver_case: AdvocateCase;
  ruling: Ruling | null;
  status: ResolutionStatus;
  review_reason: string | null;
  confidence_threshold: number;
  fraud_check: "not_implemented";
  communication_log: AgentLogEntry[];
}
