// ============================================================================
// LOGI_FRONTEND_WORKFLOW_OVERHAUL_01 — list context that survives navigation.
//
// The desks (Shipments / Contracts / Receivables / Customers / Báo Giá, …)
// held their query+filters in component useState, so the representative flow
//   lọc danh sách → mở record → thao tác → Quay lại
// threw the operator's context away and made them search from scratch.
//
// The simplest existing mechanism is the router's OWN search params
// (useSearchParams — already used by ShipmentDetail for tabs): the filter
// state travels with the route, Back restores it, and no Redux/Zustand/global
// store is introduced. Writes use replace:true so typing doesn't spam the
// history; opening a record pushes, so Back lands on the filtered list.
// ============================================================================

import { useCallback } from "react";
import { useSearchParams } from "react-router-dom";

/** One string filter (query, status, kind, …) stored in the route's params. */
export function useQueryParam(key: string): [string, (v: string) => void] {
  const [sp, setSp] = useSearchParams();
  const value = sp.get(key) ?? "";
  const set = useCallback(
    (v: string) => {
      setSp(
        (prev) => {
          const next = new URLSearchParams(prev);
          if (v) next.set(key, v);
          else next.delete(key);
          return next;
        },
        { replace: true }
      );
    },
    [setSp, key]
  );
  return [value, set];
}

/** One boolean filter stored as its presence in the route's params. */
export function useQueryFlag(key: string): [boolean, (v: boolean) => void] {
  const [sp, setSp] = useSearchParams();
  const value = sp.get(key) === "1";
  const set = useCallback(
    (v: boolean) => {
      setSp(
        (prev) => {
          const next = new URLSearchParams(prev);
          if (v) next.set(key, "1");
          else next.delete(key);
          return next;
        },
        { replace: true }
      );
    },
    [setSp, key]
  );
  return [value, set];
}
