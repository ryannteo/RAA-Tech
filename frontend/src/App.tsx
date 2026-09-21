import { useState } from "react";
import { submitDispute, type SubmitDisputePayload } from "./api/client";
import AgentTimeline from "./components/AgentTimeline";
import DisputeForm from "./components/DisputeForm";
import CaseDetails from "./components/CaseDetails";
import Header from "./components/Header";
import RulingCard from "./components/RulingCard";
import type { DisputeResult } from "./types";

export default function App() {
  const [result, setResult] = useState<DisputeResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(payload: SubmitDisputePayload) {
    setLoading(true);
    setError(null);
    setResult(null);
    try {
      setResult(await submitDispute(payload));
    } catch (e) {
      setError(e instanceof Error ? e.message : "Something went wrong");
    } finally {
      setLoading(false);
    }
  }

  function handleScenarioChange() {
    setResult(null);
    setError(null);
  }

  return (
    <div className="min-h-screen">
      <Header />
      <main className="mx-auto grid max-w-3xl gap-6 p-6">
        <DisputeForm
          onSubmit={handleSubmit}
          onScenarioChange={handleScenarioChange}
          loading={loading}
        />
        {error && <p className="text-sm text-red-600">{error}</p>}
        {result && (
          <>
            <RulingCard dispute={result} />
            <CaseDetails result={result} />
            <AgentTimeline log={result.communication_log} />
          </>
        )}
      </main>
    </div>
  );
}
