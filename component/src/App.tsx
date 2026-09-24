// ============================================================================
// Donor `App.tsx` — adapted for the component runtime:
//   * BrowserRouter → MemoryRouter: route state is component-local and does
//     not require a Python rerun for ordinary navigation (donor routing API
//     — Link/NavLink/useNavigate/useParams/useSearchParams — is unchanged).
//   * Phase B wired Home, Tasks, Shipments, Shipment Detail, Create Shipment
//     and Tracking to real Logistics data. All current navigation destinations
//     are implemented; unmatched paths render a truthful NotFound.
// ============================================================================

import { useSyncExternalStore } from "react";
import { MemoryRouter, Navigate, Route, Routes } from "react-router-dom";
import { StoreProvider } from "./lib/store";
import { getViewModel, subscribeViewModel } from "./lib/viewmodel";
import Layout from "./components/Layout";
import Home from "./pages/Home";
import Shipments from "./pages/Shipments";
import ShipmentDetail from "./pages/ShipmentDetail";
import CreateShipment from "./pages/CreateShipment";
import Receivables from "./pages/Receivables";
import PartnerPayables from "./pages/PartnerPayables";
import Customers from "./pages/Customers";
import SalesQuotes from "./pages/SalesQuotes";
import Contracts from "./pages/Contracts";
import ContractDetail from "./pages/ContractDetail";
import NewContract from "./pages/NewContract";
import TariffLookup from "./pages/TariffLookup";
import TranslationWorkspace from "./pages/TranslationWorkspace";
import PartnerContext from "./pages/PartnerContext";
import Reconciliation from "./pages/Reconciliation";
import CeoReport from "./pages/CeoReport";
import Notebook from "./pages/Notebook";
import UserAccess from "./pages/UserAccess";
import IntlPaymentTool from "./pages/IntlPaymentTool";
import NotFound from "./pages/NotFound";

function Loading() {
  return (
    <div className="min-h-[40vh] grid place-items-center">
      <p className="text-[15px] font-semibold text-slate-500">
        Đang tải dữ liệu vận hành…
      </p>
    </div>
  );
}

export default function App() {
  const vm = useSyncExternalStore(subscribeViewModel, getViewModel, getViewModel);
  return (
    <StoreProvider>
      <MemoryRouter>
        <Layout>{!vm ? <Loading /> : (
          <Routes>
            <Route path="/" element={<Home />} />
            {/* LOGI_INTERNAL_UX_SIMPLIFY_01 — compatibility redirects for the
                modules that left the normal nav. Old/bookmarked links land on
                a surviving surface instead of a dead page; the page components
                (Tasks/Tracking/Agreements) stay in the repo, unmounted, with
                their backend data untouched. */}
            <Route path="/viec-can-xu-ly" element={<Navigate to="/lo-hang" replace />} />
            <Route path="/lo-hang" element={<Shipments />} />
            <Route path="/lo-hang/:id" element={<ShipmentDetail />} />
            <Route path="/tao-lo-moi" element={<CreateShipment />} />
            <Route path="/theo-doi" element={<Navigate to="/lo-hang" replace />} />
            <Route path="/khach-hang" element={<Customers />} />
            <Route path="/tai-chinh/thu-tien" element={<Receivables />} />
            <Route path="/tai-chinh/cong-no-doi-tac" element={<PartnerPayables />} />
            <Route path="/kinh-doanh-bao-gia" element={<SalesQuotes />} />
            <Route path="/thoa-thuan-ban-giao" element={<Navigate to="/kinh-doanh-bao-gia" replace />} />
            <Route path="/hop-dong" element={<Contracts />} />
            <Route path="/hop-dong/moi" element={<NewContract />} />
            <Route path="/hop-dong/:id" element={<ContractDetail />} />
            {/* LOGI_TARIFF_LOOKUP_01 — real read-only HS/tariff lookup over
                the existing canonical reader (no longer a placeholder). */}
            <Route path="/tra-cuu-thue" element={<TariffLookup />} />
            {/* LOGI_TRANSLATION_WORKSPACE_01 — real bounded translation
                workspace over the EXISTING DeepL capability (no longer a
                placeholder; honest "chưa được cấu hình" when no key exists). */}
            <Route path="/dich-thuat" element={<TranslationWorkspace />} />
            {/* LOGI_PARTNER_CONTEXT_WORKSPACE_01 — real read-only partner-context
                workspace over the EXISTING entity-context projection, the
                authority_agents legal master and the canonical C2D payable rows
                (no longer a placeholder; no CRM surface added). */}
            <Route path="/ngu-canh-doi-tac" element={<PartnerContext />} />
            {/* LOGI_RECONCILIATION_DESK_01 — real READ-ONLY đối soát desk over the
                allocation matching core.financial_ledger already derives (no new
                ledger, no accounting engine, no write path). */}
            <Route path="/tai-chinh/doi-soat" element={<Reconciliation />} />
            {/* LOGI_CEO_REPORT_01 — bounded READ-ONLY current-position summary
                over existing Operations, C2C, C2D and reconciliation projections. */}
            <Route path="/bao-cao-ceo" element={<CeoReport />} />
            {/* LOGI_NOTEBOOK_WORKSPACE_01 — READ-ONLY handbook over reference
                material the repo already owns plus the team's own notes via the
                existing knowledge_base reader (no longer a placeholder; no CMS,
                no authoring event, no search backend). */}
            <Route path="/so-tay" element={<Notebook />} />
            {/* LOGI_INTL_PAYMENT_STANDALONE_TOOL_01 — stateless international
                payment calculator (CÔNG CỤ). No contract, no write event, no
                persistence; it left the contract detail tabs. */}
            <Route path="/thanh-toan-quoc-te" element={<IntlPaymentTool />} />
            {/* LOGI_USER_ACCESS_WORKSPACE_01 — real READ-ONLY user & access
                workspace over the EXISTING auth/user/RBAC capability (the user
                store's canonical public view, the single ROLE_PERMISSIONS
                matrix, the real AUTH_REQUIRED mode and the session identity).
                No credential material, no invented role, and deliberately no
                user-management write path: the canonical writers stay in
                core.database and none is exposed from this page yet. */}
            <Route path="/nguoi-dung" element={<UserAccess />} />
            <Route path="*" element={<NotFound />} />
          </Routes>
        )}</Layout>
      </MemoryRouter>
    </StoreProvider>
  );
}
