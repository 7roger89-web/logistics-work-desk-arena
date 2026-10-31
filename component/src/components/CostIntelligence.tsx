import { useEffect, useMemo, useState, useSyncExternalStore } from "react";
import { Archive, CheckCircle2, Database, ExternalLink, Pencil, Save, Search, TriangleAlert } from "lucide-react";
import { Field, GhostBtn, PrimaryBtn, SectionTitle, inputCls } from "./ui";
import { useStore } from "../lib/store";
import { fmtMoney } from "../lib/format";
import { loose } from "../lib/costHistory";
import { getViewModel, subscribeViewModel } from "../lib/viewmodel";
import type {
  CostCatalogEntry,
  CostMarketBenchmark,
  CostRateLine,
  CostRatePlace,
  ParsedCostRate,
} from "../lib/viewmodel";

const requestId = (prefix: string) =>
  `${prefix}-${Date.now()}-${Math.random().toString(36).slice(2, 8)}`;

const SAMPLE = `OOCL
Cước biển ningbo- HPH
USD 750/20GP
OOCL BERLIN 060W 9.27.2026
MCC USD 675/20GP
---
NINGBO-HAIPHONG
O/F:USD1425/40HQ ETD:21/09/2026 COSCO
USD1200/40HQ ETD:27/09 MSK`;

type CatalogForm = {
  id: string;
  kind: string;
  code: string;
  name: string;
  aliases: string;
  active: boolean;
  unit: string;
  group: string;
  legacyCodes: string;
  country: string;
  unlocode: string;
  zoneIds: string;
  mergedInto: string;
};

const CATALOG_KIND_LABEL: Record<string, string> = {
  SERVICE: "Dịch vụ / loại phí",
  CARRIER: "Hãng tàu / nhà vận chuyển",
  PLACE: "Địa điểm / cảng",
  ZONE: "Vùng logistics",
  UNIT: "Đơn vị tính",
  EQUIPMENT: "Container / thiết bị",
};

// The FINANCE/COST catalog is backend-owned: the browser receives every
// service name/group through the authoritative catalog slice and never keeps a
// copy of one. A blank group is therefore the honest default — the server's
// normalize_catalog_entry applies the canonical SERVICE group when the operator
// leaves it empty.
const EMPTY_CATALOG: CatalogForm = {
  id: "",
  kind: "SERVICE",
  code: "",
  name: "",
  aliases: "",
  active: true,
  unit: "Lần",
  group: "",
  legacyCodes: "",
  country: "",
  unlocode: "",
  zoneIds: "",
  mergedInto: "",
};

const splitList = (value: string) =>
  value
    .replace(/\n/g, ",")
    .split(",")
    .map((x) => x.trim())
    .filter(Boolean);

const needsReview = (row: CostRateLine) =>
  row.confidence === "NEEDS_REVIEW" ||
  row.carrier?.state === "NEEDS_REVIEW" ||
  row.equipmentState === "NEEDS_REVIEW" ||
  row.origin?.state === "NEEDS_REVIEW" ||
  row.destination?.state === "NEEDS_REVIEW";

const fiveLetterUnlocode = (value?: string) => {
  const raw = (value || "").toUpperCase().replace(/[^A-Z]/g, "");
  return raw.length === 5 ? raw : "";
};

const placeUnlocode = (place: CostRatePlace | undefined, catalog: CostCatalogEntry[]) => {
  if (!place) return "";
  const hit = catalog.find((entry) => {
    if (entry.kind !== "PLACE" || entry.active === false) return false;
    if (place.id && entry.id === place.id) return true;
    const names = [entry.code, entry.name, entry.unlocode, ...(entry.aliases || [])].filter(Boolean);
    return names.some(
      (name) => loose(String(name)) === loose(place.name) || loose(String(name)) === loose(place.raw)
    );
  });
  return (
    fiveLetterUnlocode(hit?.unlocode) ||
    fiveLetterUnlocode(hit?.code) ||
    fiveLetterUnlocode(place.name) ||
    fiveLetterUnlocode(place.raw)
  );
};

const mapLoadType = (equipment?: string) => {
  const folded = (equipment || "").toUpperCase().replace(/[^A-Z0-9]/g, "");
  if (folded === "20GP" || folded === "20" || folded === "20FT") return "container20";
  if (folded === "40HQ" || folded === "40HC") return "container40HC";
  if (folded === "40GP" || folded === "40" || folded === "40FT") return "container40";
  return "";
};

const isOceanFreightIdentity = (row: CostRateLine) => {
  // Positive Ocean Freight / O/F identity only. Container equipment is never enough.
  const fields = [row.chargeLabel, row.chargeId, row.chargeRaw];
  return fields.some((field) => {
    const token = loose(field);
    if (!token) return false;
    if (token === "of" || token === "o f" || token === "s of") return true;
    if (token === "ocean freight" || token.endsWith(" ocean freight")) return true;
    if (token === "cuoc bien" || token.endsWith(" cuoc bien")) return true;
    return /(?:^| )of$/.test(token);
  });
};

const isOceanFreightRow = (row: CostRateLine) => {
  if (row.status === "NO_SPACE" || row.kind === "AVAILABILITY") return false;
  if (needsReview(row) || row.amount == null || !row.equipment) return false;
  return isOceanFreightIdentity(row);
};

function RowEditor({
  row,
  onChange,
  onRememberPlace,
}: {
  row: CostRateLine;
  onChange: (next: CostRateLine) => void;
  onRememberPlace: (raw: string, canonical: string) => void;
}) {
  const [editing, setEditing] = useState(needsReview(row));
  const patch = (next: Partial<CostRateLine>) => onChange({ ...row, ...next });
  const setPlace = (key: "origin" | "destination", name: string) => {
    const old = row[key];
    onChange({
      ...row,
      [key]: { ...old, raw: old?.raw || name, name, state: name.trim() ? "CONFIRMED" : "UNKNOWN" },
      confidence: "CONFIRMED",
    });
  };

  if (!editing) {
    return (
      <div
        data-testid="cost-rate-row"
        className="rounded-xl border border-slate-200 bg-white px-3 py-2.5"
      >
        <div className="flex flex-wrap items-center gap-2">
          {needsReview(row) ? (
            <TriangleAlert size={16} className="text-amber-600" />
          ) : (
            <CheckCircle2 size={16} className="text-emerald-600" />
          )}
          <span className="font-bold text-[13.5px] text-slate-800">
            {row.status === "NO_SPACE"
              ? `${row.carrier?.name || "Carrier"} · KHÔNG CÓ CHỖ`
              : row.chargeLabel || "Dòng giá"}
          </span>
          {row.amount != null && (
            <span className="font-extrabold text-[13.5px] text-[#0f2a4a]">
              {row.kind === "CREDIT" ? "Hoàn/giảm " : ""}
              {fmtMoney(row.amount)} {row.currency}
              {row.equipment ? ` / ${row.equipment}` : row.unit ? ` / ${row.unit}` : ""}
            </span>
          )}
          {row.approximate && (
            <span className="rounded-full border border-amber-200 bg-amber-50 px-2 py-0.5 text-[11px] font-bold text-amber-800">
              ≈ GIÁ GẦN ĐÚNG (KHOẢNG) — XÁC NHẬN LẠI
            </span>
          )}
          {row.conditionalAmounts && row.conditionalAmounts.length > 0 && (
            <span className="rounded-full border border-amber-200 bg-amber-50 px-2 py-0.5 text-[11px] font-bold text-amber-800">
              Phụ phí có điều kiện: {row.conditionalAmounts.join(" · ")}
            </span>
          )}
          {row.carrier?.name && (
            <span className="text-[12.5px] text-slate-500">{row.carrier.name}</span>
          )}
          {(row.origin?.name || row.destination?.name) && (
            <span className="text-[12.5px] text-slate-500">
              {row.origin?.name || "—"} → {row.destination?.name || "—"}
            </span>
          )}
          <button
            type="button"
            onClick={() => setEditing(true)}
            className="ml-auto inline-flex min-h-[34px] items-center gap-1 rounded-lg border border-slate-200 px-2.5 text-[12.5px] font-bold text-slate-600"
          >
            <Pencil size={13} /> Sửa
          </button>
        </div>
        <p className="mt-1 text-[11.5px] text-slate-400 break-words">{row.rawLine}</p>
        {row.reviewNote && (
          <p className="mt-1 text-[11.5px] font-semibold text-amber-700 break-words">{row.reviewNote}</p>
        )}
      </div>
    );
  }

  return (
    <div
      data-testid="cost-rate-row-edit"
      className="rounded-xl border-2 border-amber-300 bg-amber-50/40 p-3"
    >
      <div className="grid grid-cols-1 gap-2 sm:grid-cols-2 lg:grid-cols-4">
        <Field label="Carrier">
          <input
            className={inputCls()}
            value={row.carrier?.name || ""}
            onChange={(e) =>
              patch({
                carrier: {
                  ...(row.carrier || { id: "", name: "", state: "UNKNOWN" }),
                  name: e.target.value,
                  state: e.target.value.trim() ? "CONFIRMED" : "UNKNOWN",
                },
                confidence: "CONFIRMED",
              })
            }
          />
        </Field>
        <Field label="Từ / POL">
          <input
            className={inputCls()}
            value={row.origin?.name || ""}
            onChange={(e) => setPlace("origin", e.target.value)}
          />
        </Field>
        <Field label="Đến / POD">
          <input
            className={inputCls()}
            value={row.destination?.name || ""}
            onChange={(e) => setPlace("destination", e.target.value)}
          />
        </Field>
        <Field label="Loại phí">
          <input
            className={inputCls()}
            value={row.chargeLabel || ""}
            onChange={(e) => patch({ chargeLabel: e.target.value, confidence: "CONFIRMED" })}
          />
        </Field>
        {row.status !== "NO_SPACE" && (
          <>
            <Field label="Số tiền">
              <input
                className={inputCls()}
                inputMode="decimal"
                value={row.amount == null ? "" : String(row.amount)}
                onChange={(e) => {
                  const v = e.target.value.trim();
                  const amount = v === "" ? null : Number(v);
                  const valid = amount == null || Number.isFinite(amount);
                  patch({
                    amount: valid ? amount : null,
                    confidence: v === "" || !valid ? "NEEDS_REVIEW" : "CONFIRMED",
                  });
                }}
              />
            </Field>
            <Field label="Tiền tệ">
              <input
                className={inputCls()}
                value={row.currency || ""}
                onChange={(e) => patch({ currency: e.target.value.toUpperCase(), confidence: "CONFIRMED" })}
              />
            </Field>
            <Field label="Container">
              <input
                className={inputCls()}
                placeholder="20GP / 40GP / 40HQ"
                value={row.equipment || ""}
                onChange={(e) =>
                  patch({
                    equipment: e.target.value.toUpperCase(),
                    equipmentState: e.target.value.trim() ? "CONFIRMED" : "UNKNOWN",
                    confidence: "CONFIRMED",
                  })
                }
              />
            </Field>
            <Field label="Đơn vị">
              <input
                className={inputCls()}
                value={row.unit || ""}
                onChange={(e) => patch({ unit: e.target.value.toUpperCase(), confidence: "CONFIRMED" })}
              />
            </Field>
          </>
        )}
      </div>
      <div className="mt-2 flex flex-wrap gap-2">
        {row.origin?.raw && row.origin?.name && loose(row.origin.raw) !== loose(row.origin.name) && (
          <GhostBtn
            onClick={() => onRememberPlace(row.origin.raw, row.origin.name)}
            className="min-h-[36px] px-3 text-[12px]"
          >
            Ghi nhớ “{row.origin.raw}” = {row.origin.name}
          </GhostBtn>
        )}
        {row.destination?.raw && row.destination?.name && loose(row.destination.raw) !== loose(row.destination.name) && (
          <GhostBtn
            onClick={() => onRememberPlace(row.destination.raw, row.destination.name)}
            className="min-h-[36px] px-3 text-[12px]"
          >
            Ghi nhớ “{row.destination.raw}” = {row.destination.name}
          </GhostBtn>
        )}
      </div>
      {row.reviewNote && (
        <p className="mt-2 text-[11.5px] font-semibold text-amber-700 break-words">{row.reviewNote}</p>
      )}
      <div className="mt-2 flex items-center justify-between gap-2">
        <p className="text-[11.5px] text-slate-500 break-words">
          Gốc: {row.rawLine}
        </p>
        <GhostBtn onClick={() => setEditing(false)} className="min-h-[36px] px-3 text-[12.5px]">
          Xong
        </GhostBtn>
      </div>
    </div>
  );
}

function CatalogEditor() {
  const { costIntelligence, dispatch, toast } = useStore();
  const vm = useSyncExternalStore(subscribeViewModel, getViewModel, getViewModel);
  const [form, setForm] = useState<CatalogForm>(EMPTY_CATALOG);
  const [pending, setPending] = useState<string | null>(null);

  useEffect(() => {
    if (!pending) return;
    const outcome = (vm?.lastWrites ?? []).find(
      (x) => x.event === "cost_catalog_save" && x.requestId === pending
    );
    if (!outcome) return;
    setPending(null);
    if (outcome.ok) {
      toast("Đã lưu danh mục", "Mã/tên/alias mới đã vào dữ liệu dùng chung của app.", "green");
      setForm(EMPTY_CATALOG);
    } else {
      toast("Không lưu được danh mục", outcome.error || "Backend từ chối.", "red");
    }
  }, [vm, pending, toast]);

  const edit = (entry: CostCatalogEntry) =>
    setForm({
      id: entry.id,
      kind: entry.kind,
      code: entry.code || "",
      name: entry.name || "",
      aliases: (entry.aliases || []).join(", "),
      active: entry.active !== false,
      unit: entry.unit || "Lần",
      group: entry.group || "",
      legacyCodes: (entry.legacy_codes || []).join(", "),
      country: entry.country || "",
      unlocode: entry.unlocode || "",
      zoneIds: (entry.zone_ids || []).join(", "),
      mergedInto: entry.merged_into || "",
    });

  const save = () => {
    if (!form.code.trim() && !form.name.trim()) {
      toast("Thiếu tên/mã", "Danh mục cần ít nhất tên hoặc mã.", "red");
      return;
    }
    const id = requestId("CAT");
    const sent = dispatch("cost_catalog_save", {
      id: form.id || undefined,
      kind: form.kind,
      code: form.code.trim(),
      name: form.name.trim(),
      aliases: splitList(form.aliases),
      active: form.active,
      unit: form.unit.trim(),
      group: form.group.trim(),
      legacyCodes: splitList(form.legacyCodes),
      country: form.country.trim(),
      unlocode: form.unlocode.trim(),
      zoneIds: splitList(form.zoneIds),
      mergedInto: form.mergedInto.trim(),
      requestId: id,
    });
    if (!sent) {
      toast("Không gửi được", "Component chưa kết nối backend.", "red");
      return;
    }
    setPending(id);
  };

  const list = useMemo(
    () =>
      [...costIntelligence.catalog].sort((a, b) =>
        (a.kind + a.name + a.code).localeCompare(b.kind + b.name + b.code, "vi")
      ),
    [costIntelligence.catalog]
  );

  return (
    <details className="rounded-2xl border border-slate-200 bg-white" data-testid="cost-master-data">
      <summary className="cursor-pointer px-4 py-3.5 font-extrabold text-[15px] text-[#0f2a4a]">
        DANH MỤC DỮ LIỆU — tự thêm/sửa mã, alias, carrier, địa điểm
      </summary>
      <div className="border-t border-slate-200 p-4">
        <p className="text-[13px] text-slate-500">
          Đây là dữ liệu sống. Đổi mã/tên ở đây không cần sửa code; ID nội bộ vẫn giữ nguyên để lịch sử không vỡ.
        </p>
        <div className="mt-3 grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-4">
          <Field label="Loại">
            <select className={inputCls()} value={form.kind} onChange={(e) => setForm((x) => ({ ...x, kind: e.target.value }))}>
              {["SERVICE", "CARRIER", "PLACE", "ZONE", "UNIT", "EQUIPMENT"].map((x) => (
                <option key={x} value={x}>{CATALOG_KIND_LABEL[x] || x}</option>
              ))}
            </select>
          </Field>
          <Field label="Mã">
            <input className={inputCls()} value={form.code} onChange={(e) => setForm((x) => ({ ...x, code: e.target.value.toUpperCase() }))} />
          </Field>
          <Field label="Tên">
            <input className={inputCls()} value={form.name} onChange={(e) => setForm((x) => ({ ...x, name: e.target.value }))} />
          </Field>
          <Field label="Alias / cách gọi khác">
            <input className={inputCls()} placeholder="HPH, Hai Phong, Hải Phòng" value={form.aliases} onChange={(e) => setForm((x) => ({ ...x, aliases: e.target.value }))} />
          </Field>
          {form.kind === "SERVICE" && (
            <>
              <Field label="Đơn vị mặc định">
                <input className={inputCls()} value={form.unit} onChange={(e) => setForm((x) => ({ ...x, unit: e.target.value }))} />
              </Field>
              <Field label="Nhóm">
                <input className={inputCls()} value={form.group} onChange={(e) => setForm((x) => ({ ...x, group: e.target.value }))} />
              </Field>
              <Field label="Mã cũ thay thế">
                <input className={inputCls()} placeholder="NKOF20, OF20" value={form.legacyCodes} onChange={(e) => setForm((x) => ({ ...x, legacyCodes: e.target.value }))} />
              </Field>
            </>
          )}
          {form.kind === "PLACE" && (
            <>
              <Field label="UN/LOCODE">
                <input className={inputCls()} value={form.unlocode} onChange={(e) => setForm((x) => ({ ...x, unlocode: e.target.value.toUpperCase() }))} />
              </Field>
              <Field label="Quốc gia">
                <input className={inputCls()} value={form.country} onChange={(e) => setForm((x) => ({ ...x, country: e.target.value.toUpperCase() }))} />
              </Field>
              <Field label="Logistics zone IDs">
                <input className={inputCls()} placeholder="ZONE-PRD" value={form.zoneIds} onChange={(e) => setForm((x) => ({ ...x, zoneIds: e.target.value }))} />
              </Field>
            </>
          )}
        </div>
        <div className="mt-3 flex flex-wrap items-center gap-2">
          <label className="inline-flex min-h-[44px] items-center gap-2 text-[13px] font-semibold text-slate-600">
            <input type="checkbox" checked={form.active} onChange={(e) => setForm((x) => ({ ...x, active: e.target.checked }))} />
            Đang dùng
          </label>
          <Field label="Gộp vào danh mục khác" hint="Chỉ chọn khi hai mục thực ra là một. Lịch sử cũ vẫn giữ dấu vết gốc.">
            <select
              className={inputCls()}
              value={form.mergedInto}
              onChange={(e) => setForm((x) => ({ ...x, mergedInto: e.target.value }))}
            >
              <option value="">-- Không gộp --</option>
              {costIntelligence.catalog
                .filter((entry) => entry.kind === form.kind && entry.id !== form.id && entry.active !== false)
                .sort((a, b) => (a.name + a.code).localeCompare(b.name + b.code, "vi"))
                .map((entry) => (
                  <option key={entry.id} value={entry.id}>
                    {(entry.code ? entry.code + " · " : "") + entry.name}
                  </option>
                ))}
            </select>
          </Field>
          <PrimaryBtn onClick={save} disabled={!!pending}>
            <Save size={16} /> {pending ? "ĐANG LƯU…" : form.id ? "LƯU THAY ĐỔI" : "THÊM DANH MỤC"}
          </PrimaryBtn>
          {form.id && <GhostBtn onClick={() => setForm(EMPTY_CATALOG)}>Hủy sửa</GhostBtn>}
        </div>

        {list.length > 0 && (
          <div className="mt-4 grid grid-cols-1 gap-2 md:grid-cols-2">
            {list.slice(0, 60).map((entry) => (
              <button
                type="button"
                key={entry.id}
                onClick={() => edit(entry)}
                className="touch-target rounded-xl border border-slate-200 p-3 text-left hover:bg-slate-50"
              >
                <span className="font-extrabold text-[13.5px] text-[#0f2a4a]">{CATALOG_KIND_LABEL[entry.kind] || entry.kind} · {entry.code || "—"}</span>
                <span className="block text-[13px] text-slate-600">{entry.name}</span>
                {entry.aliases?.length > 0 && <span className="block text-[11.5px] text-slate-400">Alias: {entry.aliases.join(", ")}</span>}
              </button>
            ))}
          </div>
        )}
      </div>
    </details>
  );
}

export default function CostIntelligencePanel() {
  const { costIntelligence, dispatch, toast } = useStore();
  const vm = useSyncExternalStore(subscribeViewModel, getViewModel, getViewModel);
  const [raw, setRaw] = useState("");
  const [supplier, setSupplier] = useState("");
  const [receivedOn, setReceivedOn] = useState("");
  const [parsed, setParsed] = useState<ParsedCostRate | null>(null);
  const [parsePending, setParsePending] = useState<string | null>(null);
  const [savePending, setSavePending] = useState<string | null>(null);
  const [aliasPending, setAliasPending] = useState<string | null>(null);
  const [statusPending, setStatusPending] = useState<string | null>(null);
  const [marketPending, setMarketPending] = useState<string | null>(null);
  const [marketKey, setMarketKey] = useState<string | null>(null);
  const [marketByKey, setMarketByKey] = useState<Record<string, CostMarketBenchmark>>({});

  useEffect(() => {
    if (!parsePending) return;
    const outcome = (vm?.lastWrites ?? []).find(
      (x) => x.event === "cost_rate_parse" && x.requestId === parsePending
    );
    if (!outcome) return;
    setParsePending(null);
    if (!outcome.ok) {
      toast("Chưa phân tích được", outcome.error || "Backend từ chối.", "red");
      return;
    }
    const result = outcome.parsed as ParsedCostRate | undefined;
    if (!result) {
      toast("Thiếu kết quả", "Backend không trả parsed rate.", "red");
      return;
    }
    setParsed(result);
    if (result.sourceDate) setReceivedOn(result.sourceDate);
    toast(
      "Đã bóc dữ liệu giá",
      `${result.summary.rowCount} dòng · ${result.summary.needsReview} dòng cần xem lại.`,
      result.summary.needsReview ? "amber" : "green"
    );
  }, [vm, parsePending, toast]);

  useEffect(() => {
    if (!savePending) return;
    const outcome = (vm?.lastWrites ?? []).find(
      (x) => x.event === "cost_rate_save" && x.requestId === savePending
    );
    if (!outcome) return;
    setSavePending(null);
    if (outcome.ok) {
      toast("Đã lưu vào Kho giá vốn", "Snapshot mới được thêm vào lịch sử; giá cũ không bị ghi đè.", "green");
      setRaw("");
      setParsed(null);
      setSupplier("");
      setReceivedOn("");
    } else {
      toast("Không lưu được giá", outcome.error || "Backend từ chối.", "red");
    }
  }, [vm, savePending, toast]);

  useEffect(() => {
    if (!aliasPending) return;
    const outcome = (vm?.lastWrites ?? []).find(
      (x) => x.event === "cost_catalog_save" && x.requestId === aliasPending
    );
    if (!outcome) return;
    setAliasPending(null);
    if (outcome.ok) {
      toast("Đã ghi nhớ cách gọi", "Lần sau parser sẽ dùng alias này từ danh mục chung.", "green");
    } else {
      toast("Chưa ghi nhớ được alias", outcome.error || "Backend từ chối.", "red");
    }
  }, [vm, aliasPending, toast]);

  useEffect(() => {
    if (!statusPending) return;
    const outcome = (vm?.lastWrites ?? []).find(
      (x) => x.event === "cost_rate_status_set" && x.requestId === statusPending
    );
    if (!outcome) return;
    setStatusPending(null);
    if (outcome.ok) {
      toast("Đã cập nhật trạng thái giá", "Nội dung giá gốc không bị thay đổi.", "green");
    } else {
      toast("Không đổi được trạng thái", outcome.error || "Backend từ chối.", "red");
    }
  }, [vm, statusPending, toast]);

  useEffect(() => {
    if (!marketPending) return;
    const outcome = (vm?.lastWrites ?? []).find(
      (x) => x.event === "cost_market_benchmark_fetch" && x.requestId === marketPending
    );
    if (!outcome) return;
    setMarketPending(null);
    const benchmark = outcome.benchmark as CostMarketBenchmark | undefined;
    if (!outcome.ok || !benchmark) {
      toast("Không lấy được tham khảo thị trường", outcome.error || "Backend từ chối.", "amber");
      return;
    }
    if (marketKey) {
      setMarketByKey((prev) => ({ ...prev, [marketKey]: benchmark }));
    }
    if (benchmark.status === "AVAILABLE") {
      toast("Đã lấy tham khảo thị trường", "Kết quả Freightos tách biệt với giá vốn nội bộ.", "green");
    } else if (benchmark.status === "NO_COVERAGE") {
      toast("Chưa có giá thị trường", benchmark.message || "Freightos chưa có báo giá cho tuyến này.", "amber");
    } else {
      toast("Không lấy được tham khảo thị trường", benchmark.message || "Kho giá vốn vẫn dùng bình thường.", "amber");
    }
  }, [vm, marketPending, marketKey, toast]);

  const setRateStatus = (snapshotId: string, status: string) => {
    const id = requestId("RATE-STATUS");
    if (!dispatch("cost_rate_status_set", { id: snapshotId, status, requestId: id })) {
      toast("Không gửi được", "Component chưa kết nối backend.", "red");
      return;
    }
    setStatusPending(id);
  };

  const rememberPlace = (rawName: string, canonicalName: string) => {
    const canonical = costIntelligence.catalog.find(
      (entry) =>
        entry.kind === "PLACE" &&
        entry.active !== false &&
        [entry.name, entry.code, ...(entry.aliases || [])].some(
          (value) => loose(value) === loose(canonicalName)
        )
    );
    const aliases = Array.from(new Set([...(canonical?.aliases || []), rawName]));
    const id = requestId("ALIAS");
    const sent = dispatch("cost_catalog_save", {
      id: canonical?.id || undefined,
      kind: "PLACE",
      code: canonical?.code || "",
      name: canonical?.name || canonicalName,
      aliases,
      active: true,
      country: canonical?.country || "",
      unlocode: canonical?.unlocode || "",
      zoneIds: canonical?.zone_ids || [],
      requestId: id,
    });
    if (!sent) {
      toast("Không gửi được alias", "Component chưa kết nối backend.", "red");
      return;
    }
    setAliasPending(id);
  };

  const fetchMarket = (snapshotId: string, row: CostRateLine) => {
    const originUnlocode = placeUnlocode(row.origin, costIntelligence.catalog);
    const destinationUnlocode = placeUnlocode(row.destination, costIntelligence.catalog);
    const loadType = mapLoadType(row.equipment);
    if (!originUnlocode || !destinationUnlocode || !loadType) {
      toast("Chưa đủ dữ liệu tuyến", "Cần UN/LOCODE gốc/đích và loại container đã xác nhận.", "amber");
      return;
    }
    const id = requestId("RATE-MARKET");
    const key = `${snapshotId}:${row.id}`;
    const sent = dispatch("cost_market_benchmark_fetch", {
      snapshotId,
      rowId: row.id,
      originUnlocode,
      destinationUnlocode,
      equipment: row.equipment,
      internalAmount: row.amount,
      internalCurrency: row.currency,
      requestId: id,
    });
    if (!sent) {
      toast("Không gửi được", "Component chưa kết nối backend.", "red");
      return;
    }
    setMarketKey(key);
    setMarketPending(id);
  };

  const parse = () => {
    if (!raw.trim()) {
      toast("Chưa có dữ liệu", "Dán tin nhắn/bảng giá đầu vào trước.", "red");
      return;
    }
    const id = requestId("RATE-PARSE");
    if (!dispatch("cost_rate_parse", { text: raw, receivedOn: receivedOn || undefined, requestId: id })) {
      toast("Không gửi được", "Component chưa kết nối backend.", "red");
      return;
    }
    setParsePending(id);
  };

  const updateRow = (index: number, next: CostRateLine) =>
    setParsed((old) =>
      old
        ? {
            ...old,
            rows: old.rows.map((row, i) => (i === index ? next : row)),
            summary: {
              ...old.summary,
              needsReview: old.rows
                .map((row, i) => (i === index ? next : row))
                .filter(needsReview).length,
            },
          }
        : old
    );

  const save = () => {
    if (!parsed) return;
    const unresolved = parsed.rows.filter(needsReview).length;
    if (unresolved) {
      toast(
        "Còn chỗ cần xác nhận",
        `Sửa ${unresolved} dòng màu vàng trước khi lưu để dữ liệu không học sai.`,
        "amber"
      );
      return;
    }
    const id = requestId("RATE-SAVE");
    if (
      !dispatch("cost_rate_save", {
        parsed,
        supplier: supplier.trim(),
        sourceChannel: "PASTE",
        receivedAt: receivedOn ? receivedOn + "T00:00:00Z" : undefined,
        requestId: id,
      })
    ) {
      toast("Không gửi được", "Component chưa kết nối backend.", "red");
      return;
    }
    setSavePending(id);
  };

  const recent = costIntelligence.rates.slice(0, 20);

  return (
    <div className="space-y-4" data-testid="cost-intelligence">
      <section className="rounded-2xl border border-slate-200 bg-white p-4 md:p-5">
        <SectionTitle
          icon={<Database size={18} />}
          title="Kho giá vốn"
          sub="Dán giá từ Zalo / WeChat / email → app bóc → bạn chỉ sửa chỗ chưa chắc → lưu lịch sử."
        />
        <div className="grid grid-cols-1 gap-3 lg:grid-cols-[1fr_260px]">
          <Field label="Nội dung giá đầu vào" required>
            <textarea
              data-testid="cost-rate-raw"
              rows={11}
              value={raw}
              onChange={(e) => {
                setRaw(e.target.value);
                setParsed(null);
              }}
              placeholder={SAMPLE}
              className={inputCls() + " font-mono text-[13px]"}
            />
          </Field>
          <div className="space-y-3">
            <Field label="Nguồn / người báo (nếu biết)">
              <input
                className={inputCls()}
                value={supplier}
                onChange={(e) => setSupplier(e.target.value)}
                placeholder="VD: agent A / OOCL sales"
              />
            </Field>
            <Field label="Ngày nhận / ngày bảng giá" hint="Nếu paste có một ngày riêng như 28/12/2024, app sẽ điền giúp.">
              <input
                type="date"
                data-testid="cost-rate-received-on"
                className={inputCls()}
                value={receivedOn}
                onChange={(e) => setReceivedOn(e.target.value)}
              />
            </Field>
            <div className="rounded-xl border border-blue-200 bg-blue-50 p-3 text-[12.5px] text-blue-900">
              App giữ nguyên nội dung gốc. Không có giá ≠ giá 0. “没仓位” được lưu là <b>không có chỗ</b>, không biến thành cước 0 USD.
            </div>
            <PrimaryBtn onClick={parse} disabled={!!parsePending} className="w-full" testId="cost-rate-parse">
              <Search size={17} /> {parsePending ? "ĐANG PHÂN TÍCH…" : "PHÂN TÍCH"}
            </PrimaryBtn>
          </div>
        </div>
      </section>

      {parsed && (
        <section className="rounded-2xl border border-slate-200 bg-slate-50/60 p-4" data-testid="cost-rate-review">
          <div className="flex flex-wrap items-center gap-2">
            <p className="font-extrabold text-[15.5px] text-[#0f2a4a]">REVIEW TRƯỚC KHI LƯU</p>
            <span className="rounded-full bg-white px-2.5 py-1 text-[12px] font-bold text-slate-600 border">
              {parsed.summary.rowCount} dòng
            </span>
            {parsed.summary.needsReview > 0 ? (
              <span className="rounded-full bg-amber-100 px-2.5 py-1 text-[12px] font-bold text-amber-800">
                {parsed.summary.needsReview} cần xác nhận
              </span>
            ) : (
              <span className="rounded-full bg-emerald-100 px-2.5 py-1 text-[12px] font-bold text-emerald-800">
                Sẵn sàng lưu
              </span>
            )}
          </div>
          {parsed.warnings.map((w, i) => (
            <p key={i} className="mt-2 rounded-lg border border-amber-200 bg-amber-50 px-3 py-2 text-[12.5px] font-semibold text-amber-900">
              {w}
            </p>
          ))}
          <div className="mt-3 space-y-2">
            {parsed.rows.map((row, i) => (
              <RowEditor key={row.id + i} row={row} onChange={(next) => updateRow(i, next)} onRememberPlace={rememberPlace} />
            ))}
          </div>
          <div className="mt-3 flex flex-wrap gap-2">
            <PrimaryBtn onClick={save} disabled={!!savePending || parsed.summary.needsReview > 0} testId="cost-rate-save">
              <Save size={17} /> {savePending ? "ĐANG LƯU…" : "LƯU VÀO KHO GIÁ VỐN"}
            </PrimaryBtn>
            <GhostBtn onClick={() => setParsed(null)}>Phân tích lại</GhostBtn>
          </div>
        </section>
      )}

      <section className="rounded-2xl border border-slate-200 bg-white p-4" data-testid="cost-rate-history">
        <div className="flex items-center gap-2">
          <Archive size={17} className="text-[#1e5aa8]" />
          <p className="font-extrabold text-[15px] text-[#0f2a4a]">GIÁ ĐẦU VÀO GẦN ĐÂY</p>
        </div>
        {recent.length === 0 ? (
          <p className="mt-2 text-[13.5px] text-slate-500">Chưa có snapshot giá vốn nào. Dán bảng giá đầu tiên ở phía trên.</p>
        ) : (
          <div className="mt-3 space-y-2">
            {recent.map((rate) => (
              <details key={rate.id} className="rounded-xl border border-slate-200">
                <summary className="cursor-pointer px-3 py-2.5">
                  <span className="font-extrabold text-[13.5px] text-[#0f2a4a]">{rate.supplier || "Nguồn chưa ghi"}</span>
                  <span className="ml-2 text-[12.5px] text-slate-500">{rate.received_at}</span>
                  <span className="ml-2 text-[12.5px] font-bold text-slate-500">· {rate.rows?.length || 0} dòng</span>
                </summary>
                <div className="border-t border-slate-200 p-3">
                  <div className="mb-3 grid grid-cols-1 gap-2 sm:grid-cols-[220px_1fr] sm:items-end">
                    <Field label="Trạng thái giá" hint="Chỉ đổi vòng đời; số tiền và nội dung gốc không bị sửa.">
                      <select
                        data-testid={"cost-rate-status-" + rate.id}
                        className={inputCls()}
                        value={rate.status || "ACTIVE"}
                        disabled={!!statusPending}
                        onChange={(e) => setRateStatus(rate.id, e.target.value)}
                      >
                        <option value="ACTIVE">Đang dùng</option>
                        <option value="SUPERSEDED">Đã có giá mới</option>
                        <option value="EXPIRED">Hết hạn</option>
                        <option value="WITHDRAWN">Rút lại / không dùng</option>
                      </select>
                    </Field>
                    <p className="text-[12px] text-slate-500">
                      ID: {rate.id} · Parser: {rate.parser_version}
                    </p>
                  </div>
                  {(rate.rows || []).filter((row) => isOceanFreightRow(row) && mapLoadType(row.equipment) && placeUnlocode(row.origin, costIntelligence.catalog) && placeUnlocode(row.destination, costIntelligence.catalog)).map((row) => {
                    const key = `${rate.id}:${row.id}`;
                    const market = marketByKey[key];
                    const originCode = placeUnlocode(row.origin, costIntelligence.catalog);
                    const destCode = placeUnlocode(row.destination, costIntelligence.catalog);
                    return (
                      <div
                        key={key}
                        data-testid={"cost-internal-row-" + key}
                        className="mb-3 rounded-xl border border-slate-200 bg-slate-50 p-3"
                      >
                        <p className="text-[11.5px] font-extrabold uppercase tracking-wide text-slate-500">
                          Giá vốn nội bộ
                        </p>
                        <p className="mt-1 break-words font-bold text-[13.5px] text-[#0f2a4a]">
                          {row.origin?.name || originCode} → {row.destination?.name || destCode}
                          {row.equipment ? ` · ${row.equipment}` : ""}
                          {row.carrier?.name ? ` · ${row.carrier.name}` : ""}
                          {row.amount != null ? ` · ${fmtMoney(row.amount)} ${row.currency || ""}` : ""}
                        </p>
                        <GhostBtn
                          testId={"cost-market-fetch-" + key}
                          className="mt-2 min-h-[44px] px-3 text-[13px]"
                          disabled={!!marketPending}
                          onClick={() => fetchMarket(rate.id, row)}
                        >
                          {marketPending && marketKey === key ? "ĐANG LẤY THỊ TRƯỜNG…" : "So với thị trường"}
                        </GhostBtn>
                        {market && (
                          <div
                            data-testid={"cost-market-benchmark-" + key}
                            className="mt-3 rounded-xl border-2 border-sky-300 bg-sky-50 p-3"
                          >
                            <p className="break-words font-extrabold text-[14px] text-sky-950">
                              Tham khảo thị trường · Freightos
                            </p>
                            <p className="mt-1 break-words text-[12.5px] text-sky-900">
                              {market.origin} → {market.destination} · {market.loadType}
                              {market.mode ? ` · ${market.mode}` : ""}
                            </p>
                            {market.status === "AVAILABLE" && (market.minAmount != null || market.maxAmount != null) ? (
                              <p className="mt-1 break-words font-extrabold text-[15px] text-sky-950">
                                {market.currency || "USD"} {fmtMoney(market.minAmount)} – {fmtMoney(market.maxAmount)}
                              </p>
                            ) : (
                              <p className="mt-1 break-words text-[13px] font-semibold text-amber-800">
                                {market.message || "Freightos chưa có báo giá công khai cho tuyến/thiết bị này."}
                              </p>
                            )}
                            {market.transitMin != null && market.transitMax != null && (
                              <p className="mt-1 break-words text-[12.5px] text-sky-900">
                                Transit {market.transitMin}–{market.transitMax} {market.transitUnit || "days"}
                              </p>
                            )}
                            <p className="mt-1 break-words text-[12px] text-sky-800">Lấy lúc {market.fetchedAt}</p>
                            {market.comparison && (
                              <p className="mt-1 break-words text-[12.5px] text-sky-900">
                                Nội bộ {fmtMoney(market.comparison.internalAmount)} {market.comparison.internalCurrency}
                                {market.comparison.difference != null
                                  ? ` · lệch ${fmtMoney(market.comparison.difference)} ${market.comparison.internalCurrency}`
                                  : ""}{" "}
                                ({market.comparison.label})
                              </p>
                            )}
                            <a
                              data-testid={"cost-market-attribution-" + key}
                              href={market.providerUrl || "https://ship.freightos.com"}
                              target="_blank"
                              rel="noreferrer"
                              className="mt-2 inline-flex min-h-[44px] items-center gap-1 break-words text-[12.5px] font-bold text-sky-800 underline"
                            >
                              <ExternalLink size={13} /> Nguồn: Freightos marketplace
                            </a>
                            <p className="mt-2 break-words text-[11.5px] font-semibold text-slate-600">
                              Không phải giá buy cùng hãng / cùng phụ phí với snapshot nội bộ.
                            </p>
                          </div>
                        )}
                      </div>
                    );
                  })}
                  <pre className="whitespace-pre-wrap break-words text-[11.5px] text-slate-500">{rate.raw_text}</pre>
                </div>
              </details>
            ))}
          </div>
        )}
      </section>

      <CatalogEditor />
    </div>
  );
}
