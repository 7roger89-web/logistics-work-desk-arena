import { useEffect, useMemo, useState, useSyncExternalStore } from "react";
import { Archive, CheckCircle2, Database, Pencil, Plus, Save, Search, TriangleAlert } from "lucide-react";
import { Field, GhostBtn, PrimaryBtn, SectionTitle, inputCls } from "./ui";
import { useStore } from "../lib/store";
import { fmtMoney } from "../lib/format";
import { getViewModel, subscribeViewModel } from "../lib/viewmodel";
import type {
  CostCatalogEntry,
  CostRateLine,
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
};

const EMPTY_CATALOG: CatalogForm = {
  id: "",
  kind: "SERVICE",
  code: "",
  name: "",
  aliases: "",
  active: true,
  unit: "Lần",
  group: "DỊCH VỤ XNK",
  legacyCodes: "",
  country: "",
  unlocode: "",
  zoneIds: "",
};

const splitList = (value: string) =>
  value
    .split(/[,
]/)
    .map((x) => x.trim())
    .filter(Boolean);

const needsReview = (row: CostRateLine) =>
  row.confidence === "NEEDS_REVIEW" ||
  row.equipmentState === "NEEDS_REVIEW" ||
  row.origin?.state === "NEEDS_REVIEW" ||
  row.destination?.state === "NEEDS_REVIEW";

function RowEditor({
  row,
  onChange,
}: {
  row: CostRateLine;
  onChange: (next: CostRateLine) => void;
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
                  patch({
                    amount: v === "" ? null : Number(v),
                    confidence: v === "" ? "NEEDS_REVIEW" : "CONFIRMED",
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
      group: entry.group || "DỊCH VỤ XNK",
      legacyCodes: (entry.legacy_codes || []).join(", "),
      country: entry.country || "",
      unlocode: entry.unlocode || "",
      zoneIds: (entry.zone_ids || []).join(", "),
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
                <option key={x} value={x}>{x}</option>
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
                <span className="font-extrabold text-[13.5px] text-[#0f2a4a]">{entry.kind} · {entry.code || "—"}</span>
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
  const [parsed, setParsed] = useState<ParsedCostRate | null>(null);
  const [parsePending, setParsePending] = useState<string | null>(null);
  const [savePending, setSavePending] = useState<string | null>(null);

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
    } else {
      toast("Không lưu được giá", outcome.error || "Backend từ chối.", "red");
    }
  }, [vm, savePending, toast]);

  const parse = () => {
    if (!raw.trim()) {
      toast("Chưa có dữ liệu", "Dán tin nhắn/bảng giá đầu vào trước.", "red");
      return;
    }
    const id = requestId("RATE-PARSE");
    if (!dispatch("cost_rate_parse", { text: raw, requestId: id })) {
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
            <div className="rounded-xl border border-blue-200 bg-blue-50 p-3 text-[12.5px] text-blue-900">
              App giữ nguyên nội dung gốc. Không có giá ≠ giá 0. “没仓位” được lưu là <b>không có chỗ</b>, không biến thành cước 0 USD.
            </div>
            <PrimaryBtn onClick={parse} disabled={!!parsePending} className="w-full">
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
              <RowEditor key={row.id + i} row={row} onChange={(next) => updateRow(i, next)} />
            ))}
          </div>
          <div className="mt-3 flex flex-wrap gap-2">
            <PrimaryBtn onClick={save} disabled={!!savePending || parsed.summary.needsReview > 0}>
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
