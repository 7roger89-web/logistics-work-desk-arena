// ============================================================================
// Donor `App.tsx` — adapted for the component runtime:
//   * BrowserRouter → MemoryRouter: route state is component-local and does
//     not require a Python rerun for ordinary navigation (donor routing API
//     — Link/NavLink/useNavigate/useParams/useSearchParams — is unchanged).
//   * Secondary (Phase B/C) destinations render a bounded
//     "chưa triển khai Phase A" state; the shell/navigation structure stays
//     donor-identical.
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
            <Route path="*" element={<PhaseBPlaceholder />} />
          </Routes>
        )}</Layout>
      </MemoryRouter>
    </StoreProvider>
  );
}
