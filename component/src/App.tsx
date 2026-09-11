// ============================================================================
// Donor `App.tsx` — adapted for the component runtime:
//   * BrowserRouter → MemoryRouter: route state is component-local and does
//     not require a Python rerun for ordinary navigation (donor routing API
//     — Link/NavLink/useNavigate/useParams/useSearchParams — is unchanged).
//   * Phase B wired Home, Tasks, Shipments, Shipment Detail, Create Shipment
//     and Tracking to real Logistics data. The remaining Phase C destinations
//     render a bounded "chưa triển khai" state; the shell/navigation structure
//     stays donor-identical.
// ============================================================================

import { useSyncExternalStore } from "react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { StoreProvider } from "./lib/store";
import { getViewModel, subscribeViewModel } from "./lib/viewmodel";
import Layout from "./components/Layout";
import Home from "./pages/Home";
import Tasks from "./pages/Tasks";
import Shipments from "./pages/Shipments";
import ShipmentDetail from "./pages/ShipmentDetail";
import CreateShipment from "./pages/CreateShipment";
import Tracking from "./pages/Tracking";
import Receivables from "./pages/Receivables";
import PartnerPayables from "./pages/PartnerPayables";
import Customers from "./pages/Customers";
import SalesQuotes from "./pages/SalesQuotes";
import Agreements from "./pages/Agreements";
import Contracts from "./pages/Contracts";
import ContractDetail from "./pages/ContractDetail";
import NewContract from "./pages/NewContract";
import TariffLookup from "./pages/TariffLookup";
import { PhaseBPlaceholder } from "./pages/PhaseB";

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
            <Route path="/viec-can-xu-ly" element={<Tasks />} />
            <Route path="/lo-hang" element={<Shipments />} />
            <Route path="/lo-hang/:id" element={<ShipmentDetail />} />
            <Route path="/tao-lo-moi" element={<CreateShipment />} />
            <Route path="/theo-doi" element={<Tracking />} />
            <Route path="/khach-hang" element={<Customers />} />
            <Route path="/tai-chinh/thu-tien" element={<Receivables />} />
            <Route path="/tai-chinh/cong-no-doi-tac" element={<PartnerPayables />} />
            <Route path="/kinh-doanh-bao-gia" element={<SalesQuotes />} />
            <Route path="/thoa-thuan-ban-giao" element={<Agreements />} />
            <Route path="/hop-dong" element={<Contracts />} />
            <Route path="/hop-dong/moi" element={<NewContract />} />
            <Route path="/hop-dong/:id" element={<ContractDetail />} />
            {/* LOGI_TARIFF_LOOKUP_01 — real read-only HS/tariff lookup over
                the existing canonical reader (no longer a placeholder). */}
            <Route path="/tra-cuu-thue" element={<TariffLookup />} />
            <Route path="*" element={<PhaseBPlaceholder />} />
          </Routes>
        )}</Layout>
      </MemoryRouter>
    </StoreProvider>
  );
}
