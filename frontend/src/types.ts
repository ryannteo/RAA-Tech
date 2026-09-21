export interface AgentLogEntry {
  agent: string;
  message: string;
  timestamp: string;
  data?: Record<string, unknown> | null;
}

export interface DisputeResult {
  dispute_id: string;
  category: string;
  ruling?: { decision: string; amount?: number; reasoning: string };
  confidence?: number;
  escalated?: boolean;
  communication_log: AgentLogEntry[];
  [key: string]: unknown;
}
