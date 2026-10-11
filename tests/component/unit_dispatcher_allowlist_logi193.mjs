import assert from "node:assert/strict";
import { importTs } from "./lib_loader.mjs";

// LOGI-193 B8 regression: the six template events were declared in the
// LogiEventName TYPE but missing from the runtime ALLOWED_EVENTS set, so
// dispatchLogiEvent() silently dropped every browser write/preview and the UI
// reported "Component chưa kết nối backend". RED at b737aaba (each dispatch
// returned false, spy saw nothing); GREEN once the six are allowlisted.

const { bindTransport, dispatchLogiEvent } = await importTs("dispatcher.ts");

const LOGI193_EVENTS = [
  "uploaded_template_generate",
  "docgen_template_upload",
  "docgen_template_mapping_save",
  "docgen_template_publish",
  "docgen_template_status_set",
  "docgen_template_preview",
];

// (a) a bound dispatcher spy receives EACH of the six exact events.
const seen = [];
bindTransport((event, value) => seen.push({ event, value }));
for (const name of LOGI193_EVENTS) {
  const sent = dispatchLogiEvent(name, { requestId: `B8-${name}`, templateId: "UT-qa-1" });
  assert.equal(sent, true, `${name} must pass the runtime allowlist`);
}
assert.deepEqual(
  seen.map((s) => s.event),
  LOGI193_EVENTS,
  "the spy must observe exactly the six LOGI-193 events, in order",
);
const preview = seen.find((s) => s.event === "docgen_template_preview");
assert.equal(preview.value.event, "docgen_template_preview", "transport echoes the event name");
assert.equal(preview.value.payload.templateId, "UT-qa-1", "payload carries templateId");
assert.equal(preview.value.payload.requestId, "B8-docgen_template_preview", "payload carries requestId");
assert.equal(typeof preview.value.seq, "number", "transport stamps a sequence number");
assert.ok(
  seen.every((s, i) => i === 0 || s.value.seq > seen[i - 1].value.seq),
  "sequence numbers increase across dispatches",
);

// Fail-closed: no transport bound -> nothing dispatches.
bindTransport(null);
assert.equal(
  dispatchLogiEvent("docgen_template_preview", { requestId: "B8-no-transport" }),
  false,
  "with no transport bound the event must be refused",
);

// Fail-closed: unknown events never pass, even with a live transport.
const seen2 = [];
bindTransport((event, value) => seen2.push({ event, value }));
assert.equal(dispatchLogiEvent("__not_a_real_event__", {}), false, "unknown events stay blocked");
assert.equal(seen2.length, 0, "blocked events never reach the transport");

// No regression on the pre-existing surface: a long-standing event still passes.
assert.equal(
  dispatchLogiEvent("attachment_download", { attachmentId: "ATT-1", requestId: "B8-old" }),
  true,
  "pre-existing allowlisted events keep working",
);
assert.equal(seen2[0].event, "attachment_download");

console.log(`B8 dispatcher allowlist: ${LOGI193_EVENTS.length}/6 LOGI-193 events dispatch; fail-closed intact — PASS`);
