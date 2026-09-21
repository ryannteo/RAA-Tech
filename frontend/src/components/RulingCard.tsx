import type { DisputeResult } from "../types";

export default function RulingCard({ dispute }: { dispute: DisputeResult }) {
  if (!dispute.ruling) return null;

  return (
    <div className="rounded-2xl bg-ryde-light p-4">
      <h3 className="font-semibold text-ryde-dark">Ruling</h3>
      <p className="mt-1 text-sm">
        Decision: <strong>{dispute.ruling.decision}</strong>
        {dispute.ruling.amount != null && <> — ${dispute.ruling.amount.toFixed(2)}</>}
      </p>
      <p className="mt-1 text-sm text-gray-600">{dispute.ruling.reasoning}</p>
      <p className="mt-2 text-xs text-gray-500">
        Confidence: {dispute.confidence} {dispute.escalated && "— escalated to human review"}
      </p>
    </div>
  );
}
