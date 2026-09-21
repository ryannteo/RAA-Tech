import type { AgentLogEntry } from "../types";

export default function AgentTimeline({ log }: { log: AgentLogEntry[] }) {
  if (!log.length) return null;

  return (
    <ol className="flex flex-col gap-2">
      {log.map((entry, i) => (
        <li key={i} className="rounded-xl border border-ryde-light p-3 text-sm">
          <div className="flex items-center gap-2">
            <span className="rounded-full bg-ryde-light px-2 py-0.5 text-xs font-semibold text-ryde-dark">
              {entry.agent}
            </span>
            <span className="text-xs text-gray-400">{new Date(entry.timestamp).toLocaleTimeString()}</span>
          </div>
          <p className="mt-1">{entry.message}</p>
        </li>
      ))}
    </ol>
  );
}
