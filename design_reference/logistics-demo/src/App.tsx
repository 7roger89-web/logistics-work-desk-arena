import { useState } from 'react';
import { Routes, Route } from 'react-router-dom';
import Sidebar from './components/layout/Sidebar';
import NavDrawer from './components/layout/NavDrawer';
import MobileBottomNav from './components/layout/MobileBottomNav';
import TopHeader from './components/layout/TopHeader';
import Toaster from './components/ui/Toaster';

import Dashboard from './pages/Dashboard';
import Tasks from './pages/Tasks';
import Shipments from './pages/Shipments';
import ShipmentDetail from './pages/ShipmentDetail';
import NewShipment from './pages/NewShipment';
import Tracking from './pages/Tracking';
import Customers from './pages/Customers';
import CustomerDetail from './pages/CustomerDetail';
import PartnerContext from './pages/PartnerContext';
import Quotes from './pages/Quotes';
import Agreements from './pages/Agreements';
import Contracts from './pages/Contracts';
import ContractDetail from './pages/ContractDetail';
import Finance from './pages/Finance';
import Reconciliation from './pages/Reconciliation';
import PartnerDebt from './pages/PartnerDebt';
import Reports from './pages/Reports';
import HsLookup from './pages/HsLookup';
import Handbook from './pages/Handbook';
import Translation from './pages/Translation';
import UsersPage from './pages/UsersPage';

export default function App() {
  const [drawerOpen, setDrawerOpen] = useState(false);

  return (
    <div className="flex min-h-screen bg-bg">
      <Sidebar />
      <NavDrawer open={drawerOpen} onClose={() => setDrawerOpen(false)} />
      <div className="flex-1 min-w-0 flex flex-col">
        <TopHeader onOpenDrawer={() => setDrawerOpen(true)} />
        <main className="flex-1 min-w-0 px-3 sm:px-5 lg:px-7 py-5 pb-24 lg:pb-8">
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/viec-can-xu-ly" element={<Tasks />} />
            <Route path="/lo-hang" element={<Shipments />} />
            <Route path="/lo-hang/:id" element={<ShipmentDetail />} />
            <Route path="/tao-lo-moi" element={<NewShipment />} />
            <Route path="/theo-doi-van-chuyen" element={<Tracking />} />
            <Route path="/khach-hang" element={<Customers />} />
            <Route path="/khach-hang/:id" element={<CustomerDetail />} />
            <Route path="/ngu-canh-doi-tac" element={<PartnerContext />} />
            <Route path="/kinh-doanh-bao-gia" element={<Quotes />} />
            <Route path="/thoa-thuan-ban-giao" element={<Agreements />} />
            <Route path="/hop-dong" element={<Contracts />} />
            <Route path="/hop-dong/:id" element={<ContractDetail />} />
            <Route path="/thu-tien-cong-no" element={<Finance />} />
            <Route path="/doi-soat-tai-chinh" element={<Reconciliation />} />
            <Route path="/cong-no-doi-tac" element={<PartnerDebt />} />
            <Route path="/bao-cao-ceo" element={<Reports />} />
            <Route path="/tra-cuu-thue-hs" element={<HsLookup />} />
            <Route path="/so-tay-kinh-nghiem" element={<Handbook />} />
            <Route path="/dich-thuat" element={<Translation />} />
            <Route path="/nguoi-dung" element={<UsersPage />} />
          </Routes>
        </main>
      </div>
      <MobileBottomNav onMore={() => setDrawerOpen(true)} />
      <Toaster />
    </div>
  );
}
