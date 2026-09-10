// ============================================================================
// The ONE bounded event dispatcher (React UI → Python view-model).
//
// Phase B allows exactly these typed event names; anything else is dropped
// locally and never reaches Python. No sibling-iframe communication, no
// postMessage bridge, no query-param bridge — this is the Streamlit
// Components v2 native `setTriggerValue` API.
//
// WRITE CONTRACT
// Every material event goes:
//   typed event → bounded dispatcher → current RBAC → existing writer/service
//   → audit → fresh backend read → refreshed view-model (route/tab retained).
// A local optimistic update is only ever a rendering aid; the authoritative
// value always comes back from the backend.
// ============================================================================

export type LogiEventName =
  | "shipment_update"
  | "navigate"
  | "shipment_field_save"
  | "delivery_confirm"
  | "finance_actual_save"
  | "payment_record"
  | "payment_correction"
  | "shipment_create"
  | "pxk_generate";

const ALLOWED_EVENTS: ReadonlySet<string> = new Set<LogiEventName>([
  "shipment_update",
  "navigate",
  "shipment_field_save",
  "delivery_confirm",
  "finance_actual_save",
  "payment_record",
  "payment_correction",
  "shipment_create",
  "pxk_generate",
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
): boolean {
  if (!transport || !ALLOWED_EVENTS.has(event)) return false;
  seq += 1;
  transport(event, { seq, event, payload });
  return true;
}

export function currentSeq(): number {
  return seq;
}
