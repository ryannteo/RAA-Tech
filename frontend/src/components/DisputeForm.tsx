import { useState } from "react";
import type { SubmitDisputePayload } from "../api/client";

const CATEGORIES = ["route_deviation", "no_show", "property_damage", "safety_incident"];

interface Props {
  onSubmit: (payload: SubmitDisputePayload) => void;
  loading: boolean;
}

export default function DisputeForm({ onSubmit, loading }: Props) {
  const [category, setCategory] = useState(CATEGORIES[0]);
  const [riderStatement, setRiderStatement] = useState(
    "Driver took a longer route and I was overcharged.",
  );

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    onSubmit({
      category,
      trip_id: `trip-${Date.now()}`,
      rider_id: "rider-demo",
      driver_id: "driver-demo",
      rider_statement: riderStatement,
    });
  }

  return (
    <form onSubmit={handleSubmit} className="flex flex-col gap-3 rounded-2xl border border-ryde-light p-4">
      <label className="text-sm font-medium">
        Category
        <select
          className="mt-1 w-full rounded-lg border border-gray-300 p-2"
          value={category}
          onChange={(e) => setCategory(e.target.value)}
        >
          {CATEGORIES.map((c) => (
            <option key={c} value={c}>
              {c}
            </option>
          ))}
        </select>
      </label>

      <label className="text-sm font-medium">
        Rider statement
        <textarea
          className="mt-1 w-full rounded-lg border border-gray-300 p-2"
          value={riderStatement}
          onChange={(e) => setRiderStatement(e.target.value)}
          rows={3}
        />
      </label>

      <button
        type="submit"
        disabled={loading}
        className="rounded-full bg-ryde px-4 py-2 font-semibold text-white disabled:opacity-50"
      >
        {loading ? "Running agents..." : "Submit dispute"}
      </button>
    </form>
  );
}
