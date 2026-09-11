// ============================================================================
// Donor contract `lib/store` — StoreProvider + useStore, adapted to the
// component runtime:
//   * shipments/contracts now come from the Python view-model (sandbox seed
//     in Phase A) instead of baked-in mock data;
//   * `dispatch` sends ONE typed Phase B event to the single Python
//     dispatcher; the backend performs RBAC → existing writer → audit →
//     fresh read and returns the authoritative view-model;
//   * `updateShipment` is an optimistic render aid only (legacy
//     `shipment_update` echo) and never counts as persistence;
//   * all UI state (role switcher, search, drawers, toasts) is component-
//     local, exactly as in the donor prototype.
// ============================================================================

import {
  createContext,
  useCallback,
  useContext,
  useMemo,
  useRef,
  useState,
  useSyncExternalStore,
  type ReactNode,
} from "react";
import {
  getViewModel,
  subscribeViewModel,
  unknownLabel,
  type Agreement,
  type AuthorityParty,
  type CeoReport,
  type Contract,
  type Customer,
  type Environment,
  type Home,
  type Notif,
  type PartnerPayablesViewModel,
  type ReceivablesViewModel,
  type Role,
  type Quote,
  type Shipment,
  type Task,
} from "./viewmodel";
import { dispatchLogiEvent, type LogiEventName } from "./dispatcher";

export interface Toast {
  id: number;
  title: string;
  desc?: string;
  tone: "green" | "red" | "amber" | "blue";
}

interface StoreShape {
  role: Role;
  setRole: (r: Role) => void;
  userName: string;
  query: string;
  setQuery: (q: string) => void;
  searchOpen: boolean;
  setSearchOpen: (v: boolean) => void;
  navOpen: boolean;
  setNavOpen: (v: boolean) => void;
  notifOpen: boolean;
  setNotifOpen: (v: boolean) => void;
  quickAddOpen: boolean;
  setQuickAddOpen: (v: boolean) => void;
  toasts: Toast[];
  dismissToast: (id: number) => void;
  toast: (title: string, desc?: string, tone?: Toast["tone"]) => void;
  shipments: Shipment[];
  contracts: Contract[];
  customers: Customer[];
  quotes: Quote[];
  agreements: Agreement[];
  authority: { companies: AuthorityParty[]; agents: AuthorityParty[] };
  tasks: Task[];
  notifications: Notif[];
  home: Home | null;
  environment: Environment | null;
  receivables: ReceivablesViewModel;
  payables: PartnerPayablesViewModel;
  /** LOGI_CEO_REPORT_01 — server-derived, read-only management summary. */
  ceoReport: CeoReport | null;
  unknownLabel: string;
  /**
   * Send ONE typed event to the single Python dispatcher. Persistence is
   * proven by the backend, which returns a fresh readback on the next render.
   */
  dispatch: (event: LogiEventName, payload: unknown) => boolean;
  updateShipment: (id: string, fn: (old: Shipment) => Shipment) => void;
}

const StoreContext = createContext<StoreShape | null>(null);

let toastSeq = 0;

export function StoreProvider({ children }: { children: ReactNode }) {
  const vm = useSyncExternalStore(subscribeViewModel, getViewModel, getViewModel);

  const [role, setRole] = useState<Role>(vm?.user.role ?? "SUPPORT");
  const [query, setQuery] = useState("");
  const [searchOpen, setSearchOpen] = useState(false);
  const [navOpen, setNavOpen] = useState(false);
  const [notifOpen, setNotifOpen] = useState(false);
  const [quickAddOpen, setQuickAddOpen] = useState(false);
  const [toasts, setToasts] = useState<Toast[]>([]);
  // Optimistic overrides: applied locally at once, confirmed by the
  // view-model round-trip (Python merges on the rerun).
  const [overrides, setOverrides] = useState<Record<string, Shipment>>({});

  const dismissToast = useCallback((id: number) => {
    setToasts((ts) => ts.filter((t) => t.id !== id));
  }, []);

  const toast = useCallback(
    (title: string, desc?: string, tone: Toast["tone"] = "blue") => {
      toastSeq += 1;
      const id = toastSeq;
      setToasts((ts) => [...ts.slice(-3), { id, title, desc, tone }]);
      window.setTimeout(() => dismissToast(id), 6000);
    },
    [dismissToast]
  );

  const shipments = useMemo(() => {
    const base = vm?.shipments ?? [];
    if (Object.keys(overrides).length === 0) return base;
    return base.map((s) => overrides[s.id] ?? s);
  }, [vm, overrides]);

  const contracts = useMemo(() => vm?.contracts ?? [], [vm]);
  const tasks = useMemo(() => vm?.tasks ?? [], [vm]);
  const customers = useMemo(() => vm?.customers ?? [], [vm]);
  const quotes = useMemo(() => vm?.quotes ?? [], [vm]);
  const agreements = useMemo(() => vm?.agreements ?? [], [vm]);
  const authority = useMemo(
    () => vm?.authority ?? { companies: [], agents: [] },
    [vm]
  );
  const notifications = useMemo(() => vm?.notifications ?? [], [vm]);
  const home = useMemo(() => vm?.home ?? null, [vm]);
  const environment = useMemo(() => vm?.environment ?? null, [vm]);
  const receivables = useMemo(
    () => vm?.receivables ?? { rows: [], totals: {} },
    [vm]
  );
  const payables = useMemo(
    () => vm?.payables ?? { rows: [], totals: {} },
    [vm]
  );
  const ceoReport = useMemo(() => vm?.ceoReport ?? null, [vm]);

  const dispatch = useCallback(
    (event: LogiEventName, payload: unknown) => dispatchLogiEvent(event, payload),
    []
  );

  const updateShipment = useCallback(
    (id: string, fn: (old: Shipment) => Shipment) => {
      const current =
        (vm?.shipments ?? []).find((s) => s.id === id) ??
        Object.values(overrides).find((s) => s.id === id);
      if (!current) return;
      const next = fn(current);
      // Optimistic render only. The authoritative value comes back from the
      // backend on the next view-model delivery; material writes go through
      // the typed Phase B events (`dispatch`), never through this path.
      setOverrides((o) => ({ ...o, [id]: next }));
      dispatchLogiEvent("shipment_update", { shipment: next });
    },
    [vm, overrides]
  );

  // When the server view-model confirms a change (new data arrived), the
  // overrides are superseded by the authoritative payload.
  const vmVersion = vm?.version;
  const lastVmVersion = useRef(vmVersion);
  if (vmVersion !== lastVmVersion.current) {
    lastVmVersion.current = vmVersion;
    if (vm) {
      setOverrides((o) => {
        const ids = new Set((vm.shipments ?? []).map((s) => s.id));
        const kept: Record<string, Shipment> = {};
        for (const [k, v] of Object.entries(o)) {
          const server = (vm.shipments ?? []).find((s) => s.id === k);
          // Drop override once the server copy matches it (round-trip done).
          if (server && JSON.stringify(server) === JSON.stringify(v)) continue;
          if (!ids.has(k)) continue;
          kept[k] = v;
        }
        return kept;
      });
    }
  }

  const userName = vm?.user.name ?? "—";

  const value = useMemo<StoreShape>(
    () => ({
      role,
      setRole,
      userName,
      query,
      setQuery,
      searchOpen,
      setSearchOpen,
      navOpen,
      setNavOpen,
      notifOpen,
      setNotifOpen,
      quickAddOpen,
      setQuickAddOpen,
      toasts,
      dismissToast,
      toast,
      shipments,
      contracts,
      customers,
      quotes,
      agreements,
      authority,
      tasks,
      notifications,
      home,
      environment,
      receivables,
      payables,
      ceoReport,
      unknownLabel: unknownLabel(),
      dispatch,
      updateShipment,
    }),
    [
      role,
      userName,
      query,
      searchOpen,
      navOpen,
      notifOpen,
      quickAddOpen,
      toasts,
      dismissToast,
      toast,
      shipments,
      contracts,
      customers,
      quotes,
      agreements,
      authority,
      tasks,
      notifications,
      home,
      environment,
      receivables,
      payables,
      ceoReport,
      dispatch,
      updateShipment,
    ]
  );

  return <StoreContext.Provider value={value}>{children}</StoreContext.Provider>;
}

export function useStore(): StoreShape {
  const ctx = useContext(StoreContext);
  if (!ctx) throw new Error("useStore must be used inside <StoreProvider>");
  return ctx;
}
