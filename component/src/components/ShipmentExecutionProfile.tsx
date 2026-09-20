// ============================================================================
// LOGI_SHIPMENT_EXECUTION_PROFILE_01 (issue #76) — the shipment EXECUTION
// PROFILE on /lo-hang/<id>, plus the shared progressive flow the Create-Lot
// page embeds.
//
// Owner's ruling, restated as UI behaviour: a shipment's workflow is NOT
// universal. Which stages exist — and which fields are even relevant — comes
// from THIS shipment's profile (Incoterms code + version + named place, the
// Trường Thành service scope the operator confirmed, mode, load model,
// equipment/truck facts, actual cargo insurance) and from nothing else.
//
// What this component deliberately does NOT do:
//   * it invents no business value: every selector is fed by the backend
//     projection and the generated catalog, and a blank stays blank (UNKNOWN);
//   * it never silently repairs an impossible combination: it EXPLAINS it
//     ("CẤU HÌNH CẦN KIỂM TRA") and refuses to send it;
//   * it never states "không có bảo hiểm" for an Incoterm that merely does not
//     oblige the seller: the obligation (derived) and the actual status
//     (persisted) are two separate lines;
//   * it exposes no internal schema name to the operator — only Vietnamese
//     operational wording;
//   * it does not treat "sent" as "saved": the page renders the backend's fresh
//     readback, and a refusal is shown with the backend's own explanation.
// ============================================================================

import { useEffect, useMemo, useState } from "react";
import { useSyncExternalStore } from "react";
import {
  BadgeCheck, Boxes, CircleAlert, Info, PackageCheck, Save, ShieldCheck, Truck,
} from "lucide-react";
import { Field, GhostBtn, PrimaryBtn, SectionTitle, inputCls } from "./ui";
import { getViewModel, subscribeViewModel, type ExecutionProfile, type LastWriteOutcome, type Shipment } from "../lib/viewmodel";
import { EXECUTION_PROFILE_CATALOG } from "../lib/executionProfileCatalog";
import type { LogiEventName } from "../lib/dispatcher";

export interface ProfileDraft {
  mode: string;
  incoterm: string;
  incotermVersion: string;
  namedPlace: string;
  loadModel: string;
  serviceScope: string[];
  serviceScopeConfirmed: boolean;
  insuranceStatus: string;
  insuranceArrangedBy: string;
  insuranceInsurer: string;
  insurancePolicyNo: string;
  insuranceCoverageNote: string;
}

export const EMPTY_DRAFT: ProfileDraft = {
  mode: "",
  incoterm: "",
  incotermVersion: "",
  namedPlace: "",
  loadModel: "",
  serviceScope: [],
  serviceScopeConfirmed: false,
  insuranceStatus: "",
  insuranceArrangedBy: "",
  insuranceInsurer: "",
  insurancePolicyNo: "",
  insuranceCoverageNote: "",
};

/** The draft as the backend expects it — canonical codes, never display text. */
export function draftPayload(draft: ProfileDraft) {
  // LOGI_INCOTERMS_VERSION_UX_SIMPLIFY_01: operator never chooses a year.
  // New execution profiles are implicitly 2020. A blank incoterm stays blank
  // (no EXW default); when a 2020 code is present without version, send 2020.
  const codeUpper = (draft.incoterm || "").toUpperCase();
  const current2020Codes = new Set(codesForVersion("2020"));
  const effectiveVersion =
    draft.incotermVersion || (codeUpper && current2020Codes.has(codeUpper) ? "2020" : "");
  return {
    mode: draft.mode,
    incoterm: draft.incoterm,
    incotermVersion: effectiveVersion,
    namedPlace: draft.namedPlace.trim(),
    loadModel: draft.loadModel,
    serviceScope: draft.serviceScope,
    serviceScopeConfirmed: draft.serviceScopeConfirmed,
    cargoInsurance: {
      status: draft.insuranceStatus,
      arrangedBy: draft.insuranceArrangedBy.trim(),
      insurerName: draft.insuranceInsurer.trim(),
      policyNo: draft.insurancePolicyNo.trim(),
      coverageNote: draft.insuranceCoverageNote.trim(),
    },
  };
}

/** Hydrate the draft from the backend projection (legacy payloads included). */
export function draftFromProfile(profile?: ExecutionProfile | null): ProfileDraft {
  if (!profile) return { ...EMPTY_DRAFT };
  return {
    mode: profile.mode || "",
    incoterm: profile.incoterm || "",
    incotermVersion: profile.incotermVersion || "",
    namedPlace: profile.incotermNamedPlace || "",
    loadModel: profile.loadModel || "",
    serviceScope: [...(profile.serviceScope || [])],
    serviceScopeConfirmed: Boolean(profile.serviceScopeConfirmed),
    insuranceStatus: profile.insurance?.actualStatusStated ? profile.insurance.actualStatus : "",
    insuranceArrangedBy: profile.insurance?.evidence?.arrangedBy ?? "",
    insuranceInsurer: profile.insurance?.evidence?.insurerName ?? "",
    insurancePolicyNo: profile.insurance?.evidence?.policyNo ?? "",
    insuranceCoverageNote: profile.insurance?.evidence?.coverageNote ?? "",
  };
}

// ---------------------------------------------------------------------------
// Conditional rules (client mirror of the generated catalog)
// ---------------------------------------------------------------------------

const VERSION_CODES: Set<string> = new Set(EXECUTION_PROFILE_CATALOG.versions.map((v) => String(v.code)));

// LOGI_INCOTERMS_VERSION_UX_SIMPLIFY_01: current catalog version is 2020.
// Operators never choose a year; new picker is 2020-only.
export const CURRENT_INCOTERMS_VERSION = "2020";

export function rulesForVersion(version: string): { code: string; scope: string }[] {
  const rules = (EXECUTION_PROFILE_CATALOG.rules as Record<string, readonly { code: string; scope: string }[]>)[version];
  return rules ? rules.map((row) => ({ code: row.code, scope: row.scope })) : [];
}

export function codesForVersion(version: string): string[] {
  return rulesForVersion(version).map((rule) => rule.code);
}

export function isSeaOnly(code: string, version: string): boolean {
  const effective = version || CURRENT_INCOTERMS_VERSION;
  const rule = rulesForVersion(effective).find((row) => row.code === code);
  if (rule) return rule.scope === "SEA_ONLY";
  return ["FAS", "FOB", "CFR", "CIF"].includes(code);
}

/** Current 2020 picker codes (DAT/DAF/DDU excluded for new profiles). */
export function currentIncotermCodes(): string[] {
  return codesForVersion(CURRENT_INCOTERMS_VERSION);
}

/**
 * Why an Incoterms code cannot be part of THIS execution profile — the exact
 * sentence the operator sees. `""` means the PAIR is structurally possible.
 *
 * A field the operator has not filled in yet is NOT a combination problem: that
 * is `missingProfileRequirements` below, and the two are deliberately separate
 * so a half-filled form never claims "CẤU HÌNH CẦN KIỂM TRA".
 *
 * LOGI_INCOTERMS_VERSION_UX_SIMPLIFY_01: new profiles are implicitly 2020.
 * Historical 2010 / legacy records remain readable and keep their own truth.
 */
export function combinationProblem(draft: ProfileDraft): string {
  const code = (draft.incoterm || "").toUpperCase();
  if (!code) return "";
  // Historical records keep their version truth for the pair check.
  // New profiles (no version yet) are validated as 2020.
  const effectiveVersion = draft.incotermVersion || CURRENT_INCOTERMS_VERSION;
  if (draft.incotermVersion) {
    if (!VERSION_CODES.has(draft.incotermVersion)) return "Phiên bản Incoterms chưa hợp lệ.";
    if (!codesForVersion(draft.incotermVersion).includes(code)) {
      if (code === "DAT") return "DAT là điều kiện của Incoterms 2010 — bản 2020 dùng DPU.";
      if (code === "DPU") return "DPU là điều kiện của Incoterms 2020 — bản 2010 dùng DAT.";
      if (code === "DAF" || code === "DDU") {
        return `${code} là điều kiện legacy của Incoterms 2000, không thuộc Incoterms 2010/2020.`;
      }
      return `${code} không thuộc phiên bản Incoterms đã chọn.`;
    }
  } else {
    // No version yet: validate against current 2020 set (DAT/DAF/DDU not offered).
    if (!codesForVersion(CURRENT_INCOTERMS_VERSION).includes(code)) {
      if (code === "DAT") return "DAT là điều kiện của Incoterms 2010 — bản 2020 dùng DPU.";
      if (code === "DAF" || code === "DDU") {
        return `${code} là điều kiện legacy của Incoterms 2000, không thuộc Incoterms 2010/2020.`;
      }
      return `${code} không thuộc Incoterms 2020.`;
    }
  }
  // The maritime rules (FAS/FOB/CFR/CIF) are maritime in EVERY version, so a
  // stored FOB + đường bộ is a real conflict even when the document never
  // stated a version — exactly what the backend's read-side projection says.
  if (draft.mode && isSeaOnly(code, effectiveVersion) && draft.mode !== "SEA") {
    const modeLabel = EXECUTION_PROFILE_CATALOG.modes.find((m) => m.code === draft.mode)?.label ?? draft.mode;
    return `${code} chỉ áp dụng cho chặng chính đường biển / đường thủy nội địa, không dùng cho ${modeLabel}.`;
  }
  const family = (EXECUTION_PROFILE_CATALOG.loadModels as Record<string, readonly { code: string }[]>)[draft.mode] ?? [];
  if (draft.loadModel && family.length > 0 && !family.some((row) => row.code === draft.loadModel)) {
    return `Loại hàng đã chọn không thuộc phương thức vận chuyển này.`;
  }
  return "";
}

/**
 * What the operator still has to state for the profile to be writable — the
 * same requirements the backend's write gate enforces, in Vietnamese operator
 * wording. Absent facts are reported as MISSING, never invented here.
 *
 * LOGI_INCOTERMS_VERSION_UX_SIMPLIFY_01: version is NOT a missing requirement
 * for new profiles (implicit 2020). Blank incoterm stays blank.
 */
export function missingProfileRequirements(draft: ProfileDraft): string[] {
  const family = (EXECUTION_PROFILE_CATALOG.loadModels as Record<string, readonly { code: string }[]>)[draft.mode] ?? [];
  return [
    !draft.mode && "phương thức vận chuyển",
    !draft.incoterm && "điều kiện giao hàng",
    !draft.namedPlace.trim() && "địa điểm / cảng / điểm giao",
    family.length > 0 && !draft.loadModel && "loại hàng",
    !draft.serviceScopeConfirmed && "xác nhận phạm vi Trường Thành thực hiện",
    !draft.insuranceStatus && "thực tế bảo hiểm hàng hóa",
  ].filter(Boolean) as string[];
}

// ---------------------------------------------------------------------------
// The progressive flow (steps 1..7) — shared by Create and Detail
// LOGI_INCOTERMS_VERSION_UX_SIMPLIFY_01: version step removed (implicit 2020), renumbered 1–7.
// ---------------------------------------------------------------------------

interface FieldsProps {
  draft: ProfileDraft;
  onChange: (next: ProfileDraft) => void;
  /** Rendered compactly inside the lot create form. */
  variant?: "detail" | "create";
  /** Detail page: equipment lives on the transport tab; create page has none yet. */
  onOpenEquipment?: () => void;
  equipmentSummary?: ExecutionProfile["equipment"] | null;
  truckKnown?: { known: boolean; pickupTruckType: string } | null;
  idPrefix?: string;
}

export function ExecutionProfileFields({
  draft, onChange, variant = "detail", onOpenEquipment, equipmentSummary, truckKnown, idPrefix = "profile",
}: FieldsProps) {
  const set = (patch: Partial<ProfileDraft>) => onChange({ ...draft, ...patch });
  const modeLabel = EXECUTION_PROFILE_CATALOG.modes.find((m) => m.code === draft.mode)?.label ?? "";
  // LOGI_INCOTERMS_VERSION_UX_SIMPLIFY_01: normal picker is 2020-only.
  // ANY_MODE (EXW FCA CPT CIP DAP DPU DDP) always offered; SEA_ONLY (FAS FOB CFR CIF)
  // only when mode is SEA or not yet chosen (mode filtering mandatory).
  const rules2020 = rulesForVersion(CURRENT_INCOTERMS_VERSION);
  const baseAllowed2020 = rules2020
    .filter((rule) => !(rule.scope === "SEA_ONLY" && draft.mode && draft.mode !== "SEA"))
    .map((rule) => rule.code);
  // Preserve historical code for display so legacy/DAT records remain readable
  // even though they are not in the 2020 picker.
  const historicalCode = (draft.incoterm || "").toUpperCase();
  const historicalVersion = draft.incotermVersion;
  const needsHistoricalSlot =
    historicalCode &&
    historicalVersion &&
    historicalVersion !== CURRENT_INCOTERMS_VERSION &&
    !baseAllowed2020.includes(historicalCode);
  const allowedCodes = needsHistoricalSlot ? [...baseAllowed2020, historicalCode] : baseAllowed2020;
  const hiddenCodes = rules2020
    .filter((rule) => rule.scope === "SEA_ONLY" && draft.mode && draft.mode !== "SEA")
    .map((rule) => rule.code);
  const loadFamily = (EXECUTION_PROFILE_CATALOG.loadModels as Record<string, readonly { code: string; label: string }[]>)[draft.mode] ?? [];
  const problem = combinationProblem(draft);

  const changeMode = (mode: string) => {
    const family = (EXECUTION_PROFILE_CATALOG.loadModels as Record<string, readonly { code: string }[]>)[mode] ?? [];
    const keepsLoad = !draft.loadModel || family.some((row) => row.code === draft.loadModel);
    // Use current 2020 scope for sea-only guard; historical stays readable.
    const effectiveVersionForCheck = draft.incotermVersion || CURRENT_INCOTERMS_VERSION;
    set({
      mode,
      loadModel: keepsLoad ? draft.loadModel : "",
      incoterm: isSeaOnly(draft.incoterm, effectiveVersionForCheck) && mode !== "SEA" ? "" : draft.incoterm,
    });
  };

  const summaryTruck = truckKnown ?? { known: false, pickupTruckType: "" };

  return (
    <div className="space-y-4">
      {/* 1 — PHƯƠNG THỨC VẬN CHUYỂN */}
      <div>
        <Field label="1. Phương thức vận chuyển" required hint="Chặng chính của lô: đường bộ, đường biển, hàng không hoặc đường sắt. Chưa chắc thì để trống — bổ sung sau ở chi tiết lô.">
          <select
            data-testid={`${idPrefix}-mode`}
            value={draft.mode}
            onChange={(e) => changeMode(e.target.value)}
            className={inputCls(draft.mode ? "ok" : "missing")}
          >
            <option value="">-- Bổ sung sau --</option>
            {EXECUTION_PROFILE_CATALOG.modes.map((mode) => (
              <option key={mode.code} value={mode.code}>{mode.label}</option>
            ))}
          </select>
        </Field>
      </div>

      {/* 2 — ĐIỀU KIỆN GIAO HÀNG (Incoterms 2020, mode-filtered) */}
      <div>
        <Field
          label="2. Điều kiện giao hàng"
          required
          hint={draft.mode === "SEA"
            ? "Incoterms 2020 — chặng biển hiện FAS/FOB/CFR/CIF; các phương thức đường bộ/đường không ẩn maritime."
            : draft.mode
              ? `Incoterms 2020 — chỉ hiện ${modeLabel} hợp lệ (FAS/FOB/CFR/CIF ẩn vì chỉ dùng cho đường biển).`
              : "Incoterms 2020 — chọn phương thức trước để lọc danh sách chính xác."}
        >
          <select
            data-testid={`${idPrefix}-incoterm`}
            value={draft.incoterm}
            onChange={(e) => set({ incoterm: e.target.value })}
            className={inputCls(problem && draft.incoterm ? "invalid" : draft.incoterm ? "ok" : "missing")}
          >
            <option value="">— Chưa chọn —</option>
            {allowedCodes.map((code) => (
              <option key={code} value={code}>{code}</option>
            ))}
          </select>
        </Field>
      </div>
      {hiddenCodes.length > 0 && (
        <p className="text-[12.5px] text-slate-500" data-testid={`${idPrefix}-hidden-terms`}>
          {hiddenCodes.join(" / ")} chỉ áp dụng cho đường biển / đường thủy nội địa nên không được chọn cho {modeLabel}.
        </p>
      )}
      {/* Small read-only historical note — not dominant, never a selector. */}
      {(historicalVersion === "2010" || historicalVersion === "2000_LEGACY") && (
        <p className="text-[11px] text-slate-400" data-testid={`${idPrefix}-historical-version-note`}>
          {historicalVersion === "2010"
            ? "Dữ liệu cũ · Incoterms 2010"
            : `Điều kiện legacy · ${historicalCode || "—"} (Incoterms 2000)`}
        </p>
      )}

      {/* 3 — ĐỊA ĐIỂM / CẢNG / ĐIỂM GIAO */}
      <Field
        label="3. Địa điểm / cảng / điểm giao"
        required
        hint="Địa điểm gắn với điều kiện giao hàng (kho, bãi, cảng, cửa khẩu, điểm giao). Bỏ trống = chưa xác định, hệ thống không tự suy ra."
      >
        <input
          data-testid={`${idPrefix}-named-place`}
          value={draft.namedPlace}
          onChange={(e) => set({ namedPlace: e.target.value })}
          placeholder={draft.incoterm === "FCA" ? "VD: Pingxiang Warehouse" : draft.incoterm === "CIF" ? "VD: Hai Phong Port" : draft.incoterm === "DAP" ? "VD: Bac Ninh Factory" : "VD: cửa khẩu Hữu Nghị"}
          className={inputCls(draft.namedPlace.trim() ? "ok" : "missing")}
        />
      </Field>

      {/* 5 — LOẠI HÀNG / LOAD MODEL (chỉ khi phương thức có phân loại) */}
      {draft.mode && loadFamily.length > 0 && (
        <div>
          <Field
            label="4. Loại hàng"
            required
            hint={draft.mode === "ROAD"
              ? "FTL = nguyên xe; LTL = hàng lẻ / ghép xe. Loại hàng tách biệt với loại xe."
              : draft.mode === "SEA"
                ? "FCL = container dành riêng cho lô; LCL = hàng ghép chung container với hàng khác."
                : "Hàng nguyên / trực tiếp hay hàng lẻ ghép lô."}
          >
            <select
              data-testid={`${idPrefix}-load-model`}
              value={draft.loadModel}
              onChange={(e) => set({ loadModel: e.target.value })}
              className={inputCls(draft.loadModel ? "ok" : "missing")}
            >
              <option value="">— Chưa chọn —</option>
              {loadFamily.map((row) => (
                <option key={row.code} value={row.code}>{row.label}</option>
              ))}
            </select>
          </Field>
        </div>
      )}

      {/* 6 — THIẾT BỊ / XE: chỉ khi hồ sơ thật sự cần */}
      {draft.mode === "ROAD" && draft.loadModel === "FTL" && variant === "detail" && (
        <div className="rounded-xl border border-slate-200 bg-slate-50/60 p-3.5" data-testid={`${idPrefix}-truck`}>
          <p className="font-bold text-[14px] text-[#0f2a4a] flex items-center gap-2"><Truck size={16} /> 5. Loại xe (FTL)</p>
          <p className="text-[12.5px] text-slate-500 mt-0.5">
            Đây là preset vận hành của Trường Thành, không phải quy định tải trọng: chiều dài xe không suy ra tấn/CBM/giá.
          </p>
          <div className="flex flex-wrap gap-2 mt-2.5">
            {EXECUTION_PROFILE_CATALOG.truckPresets.map((preset) => {
              const chosen = summaryTruck.pickupTruckType.trim().toUpperCase() === preset.code.toUpperCase();
              return (
                <span
                  key={preset.code}
                  className={`inline-flex items-center rounded-lg border-2 px-3 py-1.5 text-[13px] font-bold ${chosen ? "border-[#0f2a4a] bg-white text-[#0f2a4a]" : "border-slate-200 bg-white text-slate-500"}`}
                >
                  {preset.label}
                </span>
              );
            })}
          </div>
          <p className="text-[12.5px] text-slate-500 mt-2">
            {summaryTruck.known
              ? <>Đang ghi nhận: <b className="text-[#0f2a4a]">{summaryTruck.pickupTruckType || "chưa có loại xe"}</b></>
              : "Chưa có loại xe — bổ sung ở mục thông tin lấy hàng / chặng vận chuyển."}
          </p>
        </div>
      )}

      {draft.mode === "SEA" && draft.loadModel === "FCL" && variant === "detail" && (
        <div className="rounded-xl border border-slate-200 bg-slate-50/60 p-3.5" data-testid={`${idPrefix}-equipment`}>
          <p className="font-bold text-[14px] text-[#0f2a4a] flex items-center gap-2"><Boxes size={16} /> 5. Thiết bị container (FCL)</p>
          <p className="text-[12.5px] text-slate-500 mt-0.5">
            Một lô có thể dùng nhiều container; danh sách dưới đây đọc từ chính các container của lô
            (tab Vận chuyển &amp; Hàng hóa) — không có ô nhập trùng lặp.
          </p>
          {(equipmentSummary?.units?.length ?? 0) === 0 ? (
            <p className="mt-2 text-[13px] font-semibold text-amber-800">Chưa ghi nhận container nào (chưa xác định loại: 20GP / 40GP / 40HC / khác).</p>
          ) : (
            <ul className="mt-2 space-y-1">
              {equipmentSummary!.units.map((unit) => (
                <li key={unit.id || `${unit.number}-${unit.typeSize}`} className="text-[13.5px] text-[#0f2a4a]">
                  <b>{unit.typeSize || "Chưa xác định loại"}</b>
                  {unit.number ? ` · ${unit.number}` : " · chưa có số container"}
                  {unit.sealNo ? ` · seal ${unit.sealNo}` : ""}
                </li>
              ))}
            </ul>
          )}
          {onOpenEquipment && (
            <GhostBtn onClick={onOpenEquipment} className="mt-3 min-h-[44px] text-[13.5px]">
              ＋ Thêm / sửa container ở tab Vận chuyển &amp; Hàng hóa
            </GhostBtn>
          )}
        </div>
      )}

      {draft.mode === "ROAD" && draft.loadModel === "LTL" && (
        <p className="rounded-xl bg-blue-50 border border-blue-200 px-3.5 py-2.5 text-[13px] text-blue-900" data-testid={`${idPrefix}-ltl-note`}>
          Hàng lẻ / ghép xe: lô chưa có xe riêng nên không cần loại xe ở bước này.
        </p>
      )}
      {draft.mode === "SEA" && draft.loadModel === "LCL" && (
        <p className="rounded-xl bg-blue-50 border border-blue-200 px-3.5 py-2.5 text-[13px] text-blue-900" data-testid={`${idPrefix}-lcl-note`}>
          Hàng lẻ ghép container: lô không sở hữu nguyên container nên không yêu cầu số container riêng.
        </p>
      )}

      {/* 7 — PHẠM VI TRƯỜNG THÀNH THỰC HIỆN */}
      <div className="rounded-xl border-2 border-slate-200 p-3.5" data-testid={`${idPrefix}-scope`}>
        <p className="font-bold text-[14px] text-[#0f2a4a]">6. Phạm vi Trường Thành thực hiện</p>
        <p className="text-[12.5px] text-slate-500 mt-0.5">
          Incoterms chia trách nhiệm người bán / người mua. Nó KHÔNG nói Trường Thành đã được thuê làm gì —
          chỉ tích những đoạn Trường Thành thực sự làm cho lô này.
        </p>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-1.5 mt-2.5">
          {EXECUTION_PROFILE_CATALOG.serviceScope.map((segment) => {
            const checked = draft.serviceScope.includes(segment.code);
            return (
              <label
                key={segment.code}
                className={`flex items-start gap-2.5 rounded-lg border-2 px-3 py-2.5 min-h-[44px] cursor-pointer ${checked ? "border-[#1e5aa8] bg-white" : "border-slate-200 bg-white"}`}
              >
                <input
                  type="checkbox"
                  data-testid={`${idPrefix}-scope-${segment.code}`}
                  checked={checked}
                  onChange={(e) => set({
                    serviceScope: e.target.checked
                      ? EXECUTION_PROFILE_CATALOG.serviceScope.filter((row) => row.code === segment.code || draft.serviceScope.includes(row.code)).map((row) => row.code)
                      : draft.serviceScope.filter((code) => code !== segment.code),
                  })}
                  className="mt-0.5 w-5 h-5 shrink-0"
                />
                <span className="text-[13.5px] font-semibold text-[#0f2a4a] leading-snug">{segment.label}</span>
              </label>
            );
          })}
        </div>
        <label className="flex items-center gap-2.5 mt-3 min-h-[44px] cursor-pointer">
          <input
            type="checkbox"
            data-testid={`${idPrefix}-scope-confirmed`}
            checked={draft.serviceScopeConfirmed}
            onChange={(e) => set({ serviceScopeConfirmed: e.target.checked })}
            className="w-5 h-5"
          />
          <span className="text-[13.5px] font-bold text-[#0f2a4a]">Tôi đã xác nhận đúng phạm vi Trường Thành thực hiện</span>
        </label>
        {draft.serviceScope.length === 0 && draft.serviceScopeConfirmed && (
          <p className="text-[12.5px] text-amber-800 mt-1">Đã xác nhận không thực hiện đoạn nào — hãy kiểm tra lại nếu lô có phát sinh.</p>
        )}
      </div>

      {/* 8 — BẢO HIỂM HÀNG HÓA (thực tế, do người vận hành xác nhận) */}
      <div className="rounded-xl border-2 border-slate-200 p-3.5" data-testid={`${idPrefix}-insurance`}>
        <p className="font-bold text-[14px] text-[#0f2a4a] flex items-center gap-2"><ShieldCheck size={16} /> 7. Bảo hiểm hàng hóa (thực tế)</p>
        <p className="text-[12.5px] text-slate-500 mt-0.5">
          Đây là thực tế của lô, độc lập với nghĩa vụ theo Incoterms. “Chưa xác nhận” khác với “Không có bảo hiểm”.
        </p>
        <div className="flex flex-wrap gap-2 mt-2.5">
          {EXECUTION_PROFILE_CATALOG.insuranceStatuses.map((option) => {
            const chosen = draft.insuranceStatus === option.code;
            return (
              <button
                key={option.code}
                type="button"
                data-testid={`${idPrefix}-insurance-${option.code}`}
                onClick={() => set({
                  insuranceStatus: option.code,
                  ...(option.code === "YES" ? {} : {
                    insuranceArrangedBy: "", insuranceInsurer: "", insurancePolicyNo: "", insuranceCoverageNote: "",
                  }),
                })}
                className={`btn-press touch-target rounded-xl border-2 px-3.5 min-h-[44px] text-[13.5px] font-bold ${chosen ? "border-[#0f2a4a] bg-[#0f2a4a] text-white" : "border-slate-200 bg-white text-slate-600"}`}
              >
                {option.label}
              </button>
            );
          })}
        </div>
        {draft.insuranceStatus === "YES" && (
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 mt-3">
            <Field label="Đơn vị thu xếp"><input data-testid={`${idPrefix}-insurance-arranged-by`} value={draft.insuranceArrangedBy} onChange={(e) => set({ insuranceArrangedBy: e.target.value })} placeholder="VD: Trường Thành / người bán / khách" className={inputCls()} /></Field>
            <Field label="Đơn vị bảo hiểm"><input data-testid={`${idPrefix}-insurance-insurer`} value={draft.insuranceInsurer} onChange={(e) => set({ insuranceInsurer: e.target.value })} placeholder="Tên công ty bảo hiểm (nếu biết)" className={inputCls()} /></Field>
            <Field label="Số đơn / giấy chứng nhận"><input data-testid={`${idPrefix}-insurance-policy`} value={draft.insurancePolicyNo} onChange={(e) => set({ insurancePolicyNo: e.target.value })} placeholder="Để trống = chưa có" className={inputCls()} /></Field>
            <Field label="Điều kiện / ghi chú"><input data-testid={`${idPrefix}-insurance-note`} value={draft.insuranceCoverageNote} onChange={(e) => set({ insuranceCoverageNote: e.target.value })} placeholder="VD: Nhóm C / Nhóm A / phạm vi" className={inputCls()} /></Field>
          </div>
        )}
      </div>

      {problem && (
        <div role="alert" data-testid={`${idPrefix}-invalid`} className="rounded-xl border-2 border-red-300 bg-red-50 px-3.5 py-3 text-[13.5px] text-red-900">
          <p className="font-extrabold flex items-center gap-2"><CircleAlert size={16} /> CẤU HÌNH CẦN KIỂM TRA</p>
          <p className="mt-1">{problem}</p>
          <p className="mt-1 text-[12.5px]">Hệ thống không tự sửa cấu hình. Sửa lại rồi lưu, hoặc giữ nguyên dữ liệu lịch sử.</p>
        </div>
      )}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Detail page: compact summary + disclosure editor + relevant stages
// ---------------------------------------------------------------------------

interface CardProps {
  shipment: Shipment;
  dispatch: (event: LogiEventName, payload: unknown) => boolean;
  toast: (title: string, desc?: string, tone?: "green" | "red" | "amber" | "blue") => void;
  onOpenTransportTab?: () => void;
}

export function ExecutionProfileSummary({ profile }: { profile?: ExecutionProfile | null }) {
  if (!profile) {
    return (
      <div data-testid="execution-profile-summary" className="rounded-xl border border-slate-200 bg-slate-50 px-3.5 py-2.5">
        <p className="text-[13px] font-bold text-slate-600">Hồ sơ thực hiện lô: chưa có dữ liệu hồ sơ — lô cũ vẫn mở bình thường.</p>
      </div>
    );
  }
  const tone = profile.state === "CONFIG_CHECK" ? "border-red-300 bg-red-50"
    : profile.state === "PROFILE_INCOMPLETE" ? "border-amber-300 bg-amber-50"
      : "border-emerald-300 bg-emerald-50";
  const toneText = profile.state === "CONFIG_CHECK" ? "text-red-900"
    : profile.state === "PROFILE_INCOMPLETE" ? "text-amber-900" : "text-emerald-900";
  return (
    <div data-testid="execution-profile-summary" data-state={profile.state}
      className={`rounded-xl border-2 px-3.5 py-2.5 ${tone}`}>
      <p className={`text-[12px] font-extrabold tracking-wide ${toneText}`}>
        HỒ SƠ THỰC HIỆN LÔ · {profile.stateLabel}
      </p>
      <ul className="mt-1 space-y-0.5">
        {profile.summaryLines.map((line) => (
          <li key={line} className={`text-[13.5px] font-semibold ${toneText}`}>{line}</li>
        ))}
      </ul>
    </div>
  );
}

export default function ShipmentExecutionProfile({ shipment, dispatch, toast, onOpenTransportTab }: CardProps) {
  const vm = useSyncExternalStore(subscribeViewModel, getViewModel, getViewModel);
  const lastWrites: LastWriteOutcome[] = vm?.lastWrites ?? [];
  const profile = shipment.executionProfile;
  const [open, setOpen] = useState(false);
  const [pending, setPending] = useState<string>("");
  const [draft, setDraft] = useState<ProfileDraft>(() => draftFromProfile(profile));
  const revision = JSON.stringify(draftFromProfile(profile));

  // The authoritative readback resets the editor: what the operator sees is
  // always what the backend last stored — never an optimistic local guess.
  useEffect(() => { setDraft(draftFromProfile(profile)); }, [shipment.id, revision]);

  // A refusal (impossible combination, RBAC, …) arrives in the NEXT fresh
  // view-model, matched by the request identity this click sent.
  useEffect(() => {
    if (!pending) return;
    const outcome = lastWrites.find((row) => row.requestId === pending && row.event === "shipment_profile_save");
    if (!outcome) return;
    setPending("");
    if (!outcome.ok) {
      toast("Không lưu được hồ sơ lô", String(outcome.error || "Backend từ chối cấu hình này."), "red");
      return;
    }
    if (outcome.noop) {
      toast("Không có thay đổi", "Hồ sơ lô đang đúng như dữ liệu đã lưu.", "blue");
      return;
    }
    toast("Đã lưu hồ sơ lô", "Dữ liệu vừa lưu đã được đọc lại từ Logistics.", "green");
  }, [lastWrites, pending, toast]);

  const problem = useMemo(() => combinationProblem(draft), [draft]);
  const missing = useMemo(() => missingProfileRequirements(draft), [draft]);
  const stageCount = profile?.stages?.length ?? 0;

  const save = () => {
    const requestId = `profile-${Date.now().toString(36).toUpperCase()}-${Math.random().toString(36).slice(2, 7).toUpperCase()}`;
    const sent = dispatch("shipment_profile_save", {
      shipmentId: shipment.id,
      requestId,
      ...draftPayload(draft),
    });
    if (!sent) { toast("Không gửi được", "Component chưa kết nối backend.", "red"); return; }
    setPending(requestId);
    toast("Đang lưu hồ sơ lô", "Backend kiểm tra cấu hình rồi ghi và đọc lại.", "blue");
  };

  return (
    <section className="rounded-2xl bg-white border border-slate-200 p-4 md:p-5" data-testid="shipment-execution-profile">
      <SectionTitle
        icon={<PackageCheck size={19} />}
        title="Hồ sơ thực hiện lô"
        sub="Điều kiện giao hàng, phương thức, loại hàng, phạm vi Trường Thành và bảo hiểm — quyết định các bước vận hành nào thực sự có."
        right={
          <button
            type="button"
            onClick={() => setOpen((v) => !v)}
            aria-expanded={open}
            data-testid="shipment-execution-profile-toggle"
            className={`btn-press touch-target shrink-0 rounded-xl border-2 px-3.5 min-h-[44px] text-[13.5px] font-bold ${open ? "border-[#0f2a4a] bg-[#0f2a4a] text-white" : "border-slate-200 bg-white text-[#0f2a4a]"}`}
          >
            {open ? "Đóng" : "Sửa hồ sơ lô"}
          </button>
        }
      />

      <ExecutionProfileSummary profile={profile} />

      {profile?.state === "CONFIG_CHECK" && (
        <div role="alert" data-testid="execution-profile-config-check" className="mt-3 rounded-xl border-2 border-red-300 bg-red-50 px-3.5 py-3">
          <p className="font-extrabold text-[14px] text-red-900 flex items-center gap-2"><CircleAlert size={17} /> CẤU HÌNH CẦN KIỂM TRA</p>
          <ul className="mt-1.5 space-y-1">
            {profile.issues.map((issue) => (
              <li key={issue.code + issue.message} className="text-[13.5px] text-red-900">• {issue.message}</li>
            ))}
          </ul>
          <p className="mt-1.5 text-[12.5px] text-red-800">
            Dữ liệu lịch sử được giữ nguyên, không tự sửa. Chỉ khi người vận hành xác nhận lại mới ghi cấu hình mới.
          </p>
        </div>
      )}

      {profile?.stages.some((stage) => stage.mismatch) && (
        <div role="alert" data-testid="execution-profile-mismatch"
             className="mt-3 rounded-xl border-2 border-red-300 bg-red-50 px-3.5 py-3">
          <p className="font-extrabold text-[14px] text-red-900 flex items-center gap-2">
            <CircleAlert size={17} /> BẢO HIỂM: CÓ YÊU CẦU NHƯNG THỰC TẾ GHI KHÔNG CÓ
          </p>
          {profile.stages.filter((stage) => stage.mismatch).map((stage) => (
            <p key={stage.code} className="mt-1 text-[13.5px] text-red-900">{stage.missing}</p>
          ))}
          <p className="mt-1 text-[12.5px] text-red-800">
            Giữ nguyên dữ liệu thực tế đã ghi — lô chỉ hoàn thành khi chứng từ bảo hiểm được xác nhận.
          </p>
        </div>
      )}

      {!open && profile && profile.stages.length > 0 && (
        <div className="mt-3" data-testid="execution-profile-stages">
          <p className="text-[13px] font-extrabold text-[#0f2a4a]">
            Bước theo hồ sơ lô ({profile.stages.filter((s) => s.done).length}/{stageCount} đã có dữ liệu)
          </p>
          <ul className="mt-1.5 flex flex-wrap gap-1.5">
            {profile.stages.map((stage) => (
              <li
                key={stage.code}
                data-testid={`execution-profile-stage-${stage.code}`}
                data-mismatch={stage.mismatch ? "true" : "false"}
                title={`${stage.reasonLabel}: ${stage.detail}`}
                className={`inline-flex items-center gap-1.5 rounded-full border px-2.5 py-1 text-[12.5px] font-semibold ${stage.done ? "border-emerald-200 bg-emerald-50 text-emerald-900" : stage.mismatch ? "border-red-300 bg-red-50 text-red-900" : "border-amber-200 bg-amber-50 text-amber-900"}`}
              >
                {stage.done ? <BadgeCheck size={13} /> : <CircleAlert size={13} />}
                {stage.label}
              </li>
            ))}
          </ul>
        </div>
      )}

      {profile?.nextAction && (
        <p className="mt-3 text-[13.5px] text-[#0f2a4a]" data-testid="execution-profile-next-action">
          <b>Bước tiếp theo theo hồ sơ lô:</b> {profile.nextAction.label}
          <span className="text-slate-500"> · {profile.nextAction.reasonLabel}</span>
        </p>
      )}

      {open && (
        <div className="mt-4">
          {profile?.incotermAliasNote && (
            <p className="mb-3 rounded-xl border border-blue-200 bg-blue-50 px-3.5 py-2.5 text-[13px] text-blue-900">
              <Info size={14} className="inline mr-1" />
              {profile.incotermAliasNote} Chứng từ gốc vẫn giữ nguyên cách ghi cũ.
            </p>
          )}
          {profile?.incotermRawLabel && !profile.incotermAliasNote && (
            <p className="mb-3 text-[12.5px] text-slate-500">
              Hợp đồng ghi: <b>{profile.incotermRawLabel}</b> — hệ thống giữ nguyên cách ghi gốc.
            </p>
          )}
          <ExecutionProfileFields
            draft={draft}
            onChange={setDraft}
            equipmentSummary={profile?.equipment ?? null}
            truckKnown={profile?.truck ? { known: profile.truck.known, pickupTruckType: profile.truck.pickupTruckType } : null}
            onOpenEquipment={onOpenTransportTab}
          />
          {!problem && missing.length > 0 && (
            <p data-testid="profile-missing" className="mt-3 rounded-xl border border-amber-300 bg-amber-50 px-3.5 py-2.5 text-[13px] font-semibold text-amber-900">
              Hồ sơ còn thiếu: {missing.join(", ")}. Chưa lưu được cho tới khi đủ — dữ liệu đang có trong hệ thống vẫn giữ nguyên.
            </p>
          )}
          <div className="flex flex-col sm:flex-row gap-2.5 mt-4">
            <PrimaryBtn
              onClick={save}
              disabled={Boolean(problem) || missing.length > 0 || Boolean(pending)}
              testId="shipment-execution-profile-save"
              className="flex-1"
            >
              <Save size={16} /> LƯU HỒ SƠ LÔ
            </PrimaryBtn>
            <GhostBtn onClick={() => setDraft(draftFromProfile(profile))} className="min-h-[48px]">Hoàn tác bản nháp</GhostBtn>
          </div>
          {pending && (
            <p role="status" data-testid="execution-profile-pending" className="mt-2.5 rounded-lg bg-blue-50 border border-blue-200 px-3 py-2 text-[13px] font-semibold text-blue-800">
              ⏳ ĐANG CHỜ BACKEND XÁC NHẬN — chưa coi là đã lưu.
            </p>
          )}
        </div>
      )}
    </section>
  );
}
