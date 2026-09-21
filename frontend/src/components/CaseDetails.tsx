import type { ReactNode } from "react";
import type { AdvocateCase, DisputeResult, EvidenceItem } from "../types";

function EvidenceSection<T>({ title, item, children }: {
  title: string;
  item: EvidenceItem<T>;
  children: (data: T) => ReactNode;
}) {
  return (
    <section className="rounded-xl border border-ryde-light p-3">
      <h4 className="font-semibold">{title}</h4>
      {item.availability === "available"
        ? children(item.data)
        : <p className="mt-1 text-gray-600">Unavailable: {item.reason}</p>}
    </section>
  );
}

function Notes({ items }: { items: string[] }) {
  return items.length > 0 ? (
    <ul className="mt-2 list-disc space-y-1 pl-5 text-xs text-gray-500">
      {items.map((item, i) => <li key={i}>{item}</li>)}
    </ul>
  ) : null;
}

function Case({ value }: { value: AdvocateCase }) {
  return (
    <section className="rounded-2xl border border-ryde-light p-4 text-sm">
      <h3 className="font-semibold text-ryde-dark">
        {value.side === "rider" ? "Rider case" : "Driver case"}
        <span className="ml-2 text-xs font-normal">({value.source})</span>
      </h3>
      <p className="mt-2">{value.claim}</p>
      <Notes items={value.supporting_points} />
      <p className="mt-2 text-xs">Requested outcome: {value.requested_outcome}</p>
    </section>
  );
}

function time(value: string) {
  return new Date(value).toLocaleTimeString("en-SG", { timeZone: "Asia/Singapore", hour12: false });
}

function quantity(value: number | null, unit = "") {
  return value == null ? "Unavailable" : `${value}${unit}`;
}

export default function CaseDetails({ result }: { result: DisputeResult }) {
  const { evidence, policy } = result;
  return (
    <>
      <section className="grid gap-3 rounded-2xl border border-ryde-light p-4 text-sm">
        <h3 className="font-semibold text-ryde-dark">Evidence</h3>
        <p className="text-xs text-gray-500">Fixture timestamps are shown in Singapore time. Unavailable values do not mean zero.</p>
        <EvidenceSection title="GPS / telemetry" item={evidence.gps_data}>
          {(gps) => <>
            <div className="mt-2 grid grid-cols-2 gap-2">
              <p>Actual route: {quantity(gps.actual_route_km, " km")}</p>
              <p>Estimated route: {quantity(gps.estimated_route_km, " km")}</p>
              <p>Waiting: {quantity(gps.waiting_minutes, " min")}</p>
              <p>Pickup offset: {quantity(gps.pickup_distance_m, " m")}</p>
            </div>
            <ul className="mt-2 space-y-2">
              {gps.events.map((event, i) => <li key={i}>
                <span className="text-xs text-gray-500">{time(event.timestamp)} · {event.source}</span>
                <p>{event.description}</p>
              </li>)}
            </ul>
            <details className="mt-2">
              <summary className="cursor-pointer">GPS samples ({gps.points.length})</summary>
              <div className="mt-2 overflow-x-auto">
                <table className="w-full text-left text-xs">
                  <thead><tr><th>Time</th><th>Latitude</th><th>Longitude</th><th>Accuracy</th></tr></thead>
                  <tbody>{gps.points.map((point, i) => (
                    <tr key={i}><td>{time(point.timestamp)}</td><td>{point.latitude}</td><td>{point.longitude}</td><td>{point.accuracy_m} m</td></tr>
                  ))}</tbody>
                </table>
              </div>
            </details>
            <Notes items={gps.limitations} />
          </>}
        </EvidenceSection>
        <EvidenceSection title="Trip chat" item={evidence.chat_logs}>
          {(messages) => messages.length ? (
            <ol className="mt-2 space-y-2">
              {messages.map((message, i) => <li key={i}>
                <span className="text-xs text-gray-500">
                  {time(message.timestamp)} · {message.sender}
                  {" · "}{message.delivered === null ? "Delivery unknown" : message.delivered ? "Delivered" : "Not delivered"}
                </span>
                <p>{message.message}</p>
              </li>)}
            </ol>
          ) : <p className="mt-1">No chat messages recorded.</p>}
        </EvidenceSection>
        <EvidenceSection title="Fare" item={evidence.fare_data}>
          {(fare) => <>
            <dl className="mt-2 grid grid-cols-2 gap-1">
              {([
                ["Quoted total", fare.quoted_total], ["Charged total", fare.charged_total],
                ["Distance charge", fare.distance_charge], ["Cancellation fee", fare.cancellation_fee],
                ["Tolls", fare.tolls],
              ] as const).map(([label, amount]) => (
                <div key={label}><dt className="text-xs text-gray-500">{label}</dt>
                  <dd>{amount == null ? "Unavailable" : `${fare.currency} ${amount.toFixed(2)}`}</dd></div>
              ))}
            </dl>
            <Notes items={fare.limitations} />
          </>}
        </EvidenceSection>
        <EvidenceSection title="Account history" item={evidence.user_history}>
          {(history) => <>
            <div className="mt-2 grid grid-cols-2 gap-2">
              {(["rider", "driver"] as const).map((side) => <div key={side}>
                <h5 className="font-medium capitalize">{side}</h5>
                <p>Completed trips: {quantity(history[side].completed_trips)}</p>
                <p>Prior disputes: {quantity(history[side].prior_disputes)}</p>
                <p>Prior cancellations: {quantity(history[side].prior_cancellations)}</p>
              </div>)}
            </div>
            <Notes items={history.limitations} />
          </>}
        </EvidenceSection>
      </section>
      <div className="grid gap-3 sm:grid-cols-2">
        <Case value={result.rider_case} />
        <Case value={result.driver_case} />
      </div>
      <section className="rounded-2xl border border-ryde-light p-4 text-sm">
        <h3 className="font-semibold text-ryde-dark">Policy {policy.is_mock && "(mock)"}</h3>
        <p className="mt-1 text-xs text-gray-500">{policy.category} · {policy.version}</p>
        <ul className="mt-3 space-y-3">
          {policy.rules.map((rule) => <li key={rule.rule_id}>
            <h4 className="font-medium">{rule.rule_id}: {rule.title}</h4>
            <p className="mt-1 text-gray-600">{rule.text}</p>
          </li>)}
        </ul>
      </section>
    </>
  );
}
