// Exercise the production HEXA component through DOM events and model reruns.
// Run with the existing component npm dependencies: node tests/component/dom_acceptance_g15_tenant_reset.mjs
import { createRequire } from "node:module";
import { readFileSync } from "node:fs";
import assert from "node:assert/strict";
const require = createRequire(
  new URL("../../component/package.json", import.meta.url),
);
const { JSDOM } = require("jsdom");
const html = readFileSync(
  new URL("../../assets/customer_portal/hexa-portal.html", import.meta.url),
  "utf8",
);
const js = readFileSync(
  new URL("../../assets/customer_portal/hexa-portal.js", import.meta.url),
  "utf8",
);
const dom = new JSDOM(`<div id="root">${html}</div>`, {
  pretendToBeVisual: true,
});
globalThis.document = dom.window.document;
globalThis.window = dom.window;
globalThis.requestAnimationFrame = dom.window.requestAnimationFrame.bind(
  dom.window,
);
const { default: mount } = await import(
  "data:text/javascript;base64," + Buffer.from(js).toString("base64")
);
const root = document.querySelector("#root");
const secret = "PRIVATE-PRIOR-TENANT";
const lot = {
  shipment_id: secret,
  transport_mode: "SEA",
  verified_stage_title: secret,
  documents: [{ id: secret, title: secret, kind: "PL", version: "v2" }],
  timeline: [{ title: secret, stage: "pickup", occurred_at: "2026-10-30" }],
  journey: {
    nodes: [
      {
        id: "pickup",
        index: "01",
        label: "Lấy hàng",
        state: "COMPLETED",
        evidence: secret,
      },
    ],
    edges: [],
  },
  publication: { version: "v1", approved_at: "2026-10-30" },
};
const paint = (lots) =>
  mount({
    parentElement: root,
    data: { model: { customer: { name: "QA" }, lots } },
  });
function openOldModal() {
  paint([lot]);
  root.querySelector("#btn-global-docs").click();
  assert.equal(
    root.querySelector("#journey-modal-layer").classList.contains("hidden"),
    false,
  );
  assert(root.textContent.includes(secret));
}
function assertCleared() {
  assert(
    root.querySelector("#journey-modal-layer").classList.contains("hidden"),
  );
  assert(
    !root.textContent.includes(secret),
    "previous tenant data survived in DOM",
  );
  root.querySelector("#btn-global-docs").click();
  assert(
    root.querySelector("#journey-modal-layer").classList.contains("hidden"),
    "stale lot can reopen",
  );
}
openOldModal();
paint([]); // no published shipments, including revocation of the current release
assertCleared();
openOldModal();
paint([
  {
    ...lot,
    shipment_id: "NEW-LOT",
    verified_stage_title: "NEW",
    documents: [],
    timeline: [],
    journey: { nodes: [], edges: [] },
  },
]);
assert(root.querySelector("#journey-modal-layer").classList.contains("hidden"));
assert(
  !root.textContent.includes(secret),
  "previous modal survived replacement with one lot",
);
assert(root.textContent.includes("NEW-LOT"));
openOldModal();
const other = {
  ...lot,
  shipment_id: "OTHER",
  verified_stage_title: "NEW",
  documents: [],
  timeline: [],
  journey: { nodes: [], edges: [] },
};
paint([other, { ...other, shipment_id: "OTHER-2" }]);
assertCleared();
assert(root.textContent.includes("OTHER-2"));
console.log(
  "PASS G1.5 tenant/revocation model rerun clears stale data (0, 1, 2 lots)",
);
dom.window.close();
