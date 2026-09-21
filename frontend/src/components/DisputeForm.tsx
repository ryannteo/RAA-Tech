import { useEffect, useState } from "react";
import { listScenarios } from "../api/client";
import type { ScenarioSummary, SubmitDisputePayload } from "../types";

interface Props {
  onSubmit: (payload: SubmitDisputePayload) => void;
  onScenarioChange: () => void;
  loading: boolean;
}

export default function DisputeForm({ onSubmit, onScenarioChange, loading }: Props) {
  const [scenarios, setScenarios] = useState<ScenarioSummary[]>([]);
  const [selectedId, setSelectedId] = useState("");
  const [scenarioError, setScenarioError] = useState<string | null>(null);
  const [riderStatement, setRiderStatement] = useState("");
  const [driverStatement, setDriverStatement] = useState("");
  const selected = scenarios.find((scenario) => scenario.scenario_id === selectedId);

  useEffect(() => {
    let active = true;
    listScenarios().then((items) => {
      if (active) {
        setScenarios(items);
        setSelectedId(items[0]?.scenario_id ?? "");
        if (!items.length) setScenarioError("No demo scenarios are available.");
      }
    }).catch((error: unknown) => {
      if (active) setScenarioError(error instanceof Error ? error.message : "Unable to load scenarios.");
    });
    return () => { active = false; };
  }, []);

  function handleSubmit(event: React.FormEvent) {
    event.preventDefault();
    if (!selected) return;
    onSubmit({
      scenario_id: selected.scenario_id,
      category: selected.category,
      rider_statement: riderStatement.trim() || null,
      driver_statement: driverStatement.trim() || null,
    });
  }

  return (
    <form onSubmit={handleSubmit} className="flex flex-col gap-3 rounded-2xl border border-ryde-light p-4">
      <label className="text-sm font-medium">
        Demo scenario
        <select
          className="mt-1 w-full rounded-lg border border-gray-300 p-2"
          value={selectedId}
          disabled={loading || !scenarios.length}
          onChange={(event) => {
            setSelectedId(event.target.value);
            setRiderStatement("");
            setDriverStatement("");
            onScenarioChange();
          }}
        >
          {!scenarios.length && <option value="">Loading scenarios...</option>}
          {scenarios.map((scenario) => (
            <option key={scenario.scenario_id} value={scenario.scenario_id}>{scenario.title}</option>
          ))}
        </select>
      </label>
      {scenarioError && <p role="alert" className="text-sm text-red-600">{scenarioError}</p>}
      {selected && (
        <p className="text-sm text-gray-600">
          {selected.description}<br />
          <span className="text-xs">{selected.scenario_id} · {selected.category}</span>
        </p>
      )}
      <label className="text-sm font-medium">
        Rider statement (optional)
        <textarea
          className="mt-1 w-full rounded-lg border border-gray-300 p-2"
          value={riderStatement}
          disabled={loading}
          onChange={(event) => setRiderStatement(event.target.value)}
          rows={3}
        />
      </label>
      <label className="text-sm font-medium">
        Driver statement (optional)
        <textarea
          className="mt-1 w-full rounded-lg border border-gray-300 p-2"
          value={driverStatement}
          disabled={loading}
          onChange={(event) => setDriverStatement(event.target.value)}
          rows={3}
        />
      </label>
      <p className="text-xs text-gray-500">
        Demo data and policy. Advocate and judge outputs are stubs; statements do not change the preset ruling.
      </p>
      <button
        type="submit"
        disabled={loading || !selected}
        className="rounded-full bg-ryde px-4 py-2 font-semibold text-white disabled:opacity-50"
      >
        {loading ? "Running demo..." : "Submit dispute"}
      </button>
    </form>
  );
}
