// ============================================================================
// The ONE bounded event dispatcher (React UI → Python view-model).
//
// Phase A allows exactly these event names; anything else is dropped locally.
// No sibling-iframe communication, no postMessage bridge, no query-param
// bridge — this is the Streamlit Components v2 native `setTriggerValue` API.
// ============================================================================

export type LogiEventName = "shipment_update" | "navigate";

const ALLOWED_EVENTS: ReadonlySet<string> = new Set<LogiEventName>([
  "shipment_update",
  "navigate",
]);

type Transport = (event: string, value: unknown) => void;

let transport: Transport | null = null;
let seq = 0;

/** Bind the v2 component transport (called once per component invocation). */
export function bindTransport(t: Transport | null): void {
  transport = t;
}

export function dispatchLogiEvent(
  event: LogiEventName,
  payload: unknown
): void {
  if (!transport || !ALLOWED_EVENTS.has(event)) return;
  seq += 1;
  transport(event, { seq, event, payload });
}
