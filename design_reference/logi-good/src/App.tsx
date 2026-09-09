import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { StoreProvider } from "./lib/store";
import Layout from "./components/Layout";
import Home from "./pages/Home";
import Tasks from "./pages/Tasks";
import Shipments from "./pages/Shipments";
import ShipmentDetail from "./pages/ShipmentDetail";
import Contracts from "./pages/Contracts";
import ContractDetail from "./pages/ContractDetail";
import NewContract from "./pages/NewContract";
import { Customers, PartnerContext } from "./pages/Customers";
import { Quotes, Agreements } from "./pages/Sales";
import { Collect, Reconcile, PartnerDebt } from "./pages/Finance";
import CEO from "./pages/CEO";
import { Tracking, NewLot, HSLookup, Handbook, Translate, Users } from "./pages/Tools";

export default function App() {
  return (
    <StoreProvider>
      <BrowserRouter>
        <Layout>
          <Routes>
            <Route path="/" element={<Home />} />
            <Route path="/viec-can-xu-ly" element={<Tasks />} />
            <Route path="/lo-hang" element={<Shipments />} />
            <Route path="/lo-hang/:id" element={<ShipmentDetail />} />
            <Route path="/tao-lo-moi" element={<NewLot />} />
            <Route path="/theo-doi" element={<Tracking />} />
            <Route path="/khach-hang" element={<Customers />} />
            <Route path="/ngu-canh-doi-tac" element={<PartnerContext />} />
            <Route path="/kinh-doanh-bao-gia" element={<Quotes />} />
            <Route path="/thoa-thuan-ban-giao" element={<Agreements />} />
            <Route path="/hop-dong" element={<Contracts />} />
            <Route path="/hop-dong/moi" element={<NewContract />} />
            <Route path="/hop-dong/:id" element={<ContractDetail />} />
            <Route path="/tai-chinh/thu-tien" element={<Collect />} />
            <Route path="/tai-chinh/doi-soat" element={<Reconcile />} />
            <Route path="/tai-chinh/cong-no-doi-tac" element={<PartnerDebt />} />
            <Route path="/bao-cao-ceo" element={<CEO />} />
            <Route path="/tra-cuu-thue" element={<HSLookup />} />
            <Route path="/so-tay" element={<Handbook />} />
            <Route path="/dich-thuat" element={<Translate />} />
            <Route path="/nguoi-dung" element={<Users />} />
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </Layout>
      </BrowserRouter>
    </StoreProvider>
  );
}
