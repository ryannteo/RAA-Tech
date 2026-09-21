import type { DisputeResult } from "../types";

export default function RulingCard({ dispute }: { dispute: DisputeResult }) {
  const { ruling } = dispute;
  return (
    <section className="rounded-2xl bg-ryde-light p-4" aria-live="polite">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <h3 className="font-semibold text-ryde-dark">Ruling</h3>
        <span className="rounded-full bg-white px-3 py-1 text-sm font-semibold">{dispute.status}</span>
      </div>
      <p className="mt-1 text-xs text-gray-600">{dispute.dispute.scenario_id} · {dispute.dispute.trip_id}</p>
      {ruling ? (
        <>
          <p className="mt-2 text-xs font-semibold text-ryde-dark">
            {ruling.source === "stub" ? "Demo stub ruling" : "AI ruling"}
          </p>
          <p className="mt-1 text-sm">
            Decision: <strong>{ruling.decision}</strong>
            {ruling.amount != null
              ? <> — {ruling.currency} {ruling.amount.toFixed(2)}</>
              : <> — amount unavailable</>}
          </p>
          <p className="mt-1 text-sm text-gray-600">{ruling.reasoning}</p>
          <p className="mt-2 text-sm">
            Confidence: {ruling.confidence}
            {" · "}Resolution threshold: {dispute.confidence_threshold}
          </p>
        </>
      ) : <p className="mt-2 text-sm">No valid ruling. Confidence is unavailable.</p>}
      {dispute.review_reason && <p className="mt-2 text-sm">{dispute.review_reason}</p>}
      {dispute.status === "needs_review" && (
        <p className="mt-1 text-xs text-gray-600">Review required. No human decision has been recorded.</p>
      )}
    </section>
  );
}
