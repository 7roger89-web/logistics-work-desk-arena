import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { PackagePlus } from 'lucide-react';
import { useAppData } from '../lib/dataContext';
import { ROUTES, BORDERS, GOODS_TYPES } from '../lib/mockData';
import PageHeader from '../components/ui/PageHeader';
import Card, { CardTitle } from '../components/ui/Card';
import Button from '../components/ui/Button';

export default function NewShipment() {
  const navigate = useNavigate();
  const { customers, contracts, addShipment } = useAppData();
  const [customerId, setCustomerId] = useState('');
  const [contractId, setContractId] = useState('');
  const [route, setRoute] = useState(ROUTES[0]);
  const [border, setBorder] = useState(BORDERS[0]);
  const [factoryName, setFactoryName] = useState('');
  const [factoryAddress, setFactoryAddress] = useState('');
  const [factoryContact, setFactoryContact] = useState('');
  const [factoryPhone, setFactoryPhone] = useState('');
  const [pickupTime, setPickupTime] = useState('');
  const [goodsType, setGoodsType] = useState(GOODS_TYPES[0]);
  const [packages, setPackages] = useState('');
  const [weightKg, setWeightKg] = useState('');
  const [cbm, setCbm] = useState('');
  const [sale, setSale] = useState('Lê Minh Anh');
  const [support, setSupport] = useState('Nguyễn Thị Hải');

  const customer = customers.find((c) => c.id === customerId);
  const customerContracts = contracts.filter((c) => c.customerId === customerId);
  const canSubmit = customerId && factoryName && pickupTime;

  function handleSubmit() {
    if (!customer) return;
    const linkedContract = customerContracts.find((c) => c.id === contractId);
    const id = addShipment({
      customerId: customer.id,
      customer: customer.name,
      contractId: linkedContract?.id,
      contractNo: linkedContract ? (linkedContract.type === 'HDMB' ? linkedContract.id : `${linkedContract.id}${linkedContract.pl ? ' / ' + linkedContract.pl.soPL : ''}`) : undefined,
      route, border, sale, support,
      factory: { name: factoryName, address: factoryAddress, contact: factoryContact, phone: factoryPhone, pickupTime },
      goods: { packages: Number(packages) || 0, weightKg: Number(weightKg) || 0, dimensions: '', cbm: Number(cbm) || 0, goodsType, note: '' },
    });
    navigate(`/lo-hang/${id}`);
  }

  return (
    <div className="max-w-3xl">
      <PageHeader title="Tạo Lô Mới" subtitle="Nhập thông tin cơ bản để mở hồ sơ vận hành cho lô hàng. Bạn có thể bổ sung chi tiết sau trong Shipment Workspace." />

      <div className="space-y-4">
        <Card>
          <CardTitle>1. Khách hàng &amp; Hợp đồng</CardTitle>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <div className="text-[12.5px] font-medium text-ink-400 mb-1">Khách hàng *</div>
              <select value={customerId} onChange={(e) => { setCustomerId(e.target.value); setContractId(''); }} className="w-full h-11 rounded-xl border border-slate-300 px-3 text-[14px]">
                <option value="">— Chọn khách hàng —</option>
                {customers.map((c) => <option key={c.id} value={c.id}>{c.name}</option>)}
              </select>
            </div>
            <div>
              <div className="text-[12.5px] font-medium text-ink-400 mb-1">Hợp đồng liên kết (nếu có)</div>
              <select value={contractId} onChange={(e) => setContractId(e.target.value)} disabled={!customerId} className="w-full h-11 rounded-xl border border-slate-300 px-3 text-[14px] disabled:bg-slate-50 disabled:text-ink-400">
                <option value="">Chưa có — sẽ bổ sung sau</option>
                {customerContracts.map((c) => <option key={c.id} value={c.id}>{c.id} ({c.type})</option>)}
              </select>
            </div>
          </div>
        </Card>

        <Card>
          <CardTitle>2. Tuyến vận chuyển</CardTitle>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <div className="text-[12.5px] font-medium text-ink-400 mb-1">Tuyến *</div>
              <select value={route} onChange={(e) => setRoute(e.target.value)} className="w-full h-11 rounded-xl border border-slate-300 px-3 text-[14px]">
                {ROUTES.map((r) => <option key={r} value={r}>{r}</option>)}
              </select>
            </div>
            <div>
              <div className="text-[12.5px] font-medium text-ink-400 mb-1">Cửa khẩu *</div>
              <select value={border} onChange={(e) => setBorder(e.target.value)} className="w-full h-11 rounded-xl border border-slate-300 px-3 text-[14px]">
                {BORDERS.map((b) => <option key={b} value={b}>{b}</option>)}
              </select>
            </div>
          </div>
        </Card>

        <Card>
          <CardTitle>3. Nhà máy lấy hàng</CardTitle>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <Input label="Tên nhà máy *" value={factoryName} onChange={setFactoryName} />
            <Input label="Thời gian lấy hàng dự kiến *" value={pickupTime} onChange={setPickupTime} placeholder="dd/mm/yyyy hh:mm" />
            <Input label="Địa chỉ" value={factoryAddress} onChange={setFactoryAddress} className="sm:col-span-2" />
            <Input label="Người liên hệ" value={factoryContact} onChange={setFactoryContact} />
            <Input label="Điện thoại" value={factoryPhone} onChange={setFactoryPhone} />
          </div>
        </Card>

        <Card>
          <CardTitle>4. Thông tin hàng hoá cơ bản</CardTitle>
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
            <div className="col-span-2 sm:col-span-1">
              <div className="text-[12.5px] font-medium text-ink-400 mb-1">Loại hàng</div>
              <select value={goodsType} onChange={(e) => setGoodsType(e.target.value)} className="w-full h-11 rounded-xl border border-slate-300 px-3 text-[14px]">
                {GOODS_TYPES.map((g) => <option key={g} value={g}>{g}</option>)}
              </select>
            </div>
            <Input label="Số kiện" value={packages} onChange={(v) => setPackages(v.replace(/[^0-9]/g, ''))} />
            <Input label="Trọng lượng (kg)" value={weightKg} onChange={(v) => setWeightKg(v.replace(/[^0-9]/g, ''))} />
            <Input label="CBM" value={cbm} onChange={(v) => setCbm(v.replace(/[^0-9.]/g, ''))} />
          </div>
        </Card>

        <Card>
          <CardTitle>5. Phân công phụ trách</CardTitle>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <Input label="Sale phụ trách" value={sale} onChange={setSale} />
            <Input label="Support phụ trách" value={support} onChange={setSupport} />
          </div>
        </Card>

        <div className="sticky bottom-20 lg:bottom-4 bg-bg/0">
          <Button size="lg" full icon={<PackagePlus size={19} />} disabled={!canSubmit} onClick={handleSubmit}>✅ TẠO LÔ HÀNG</Button>
          {!canSubmit && <p className="text-center text-[12.5px] text-warning-600 font-medium mt-2">Vui lòng chọn khách hàng, nhập tên nhà máy và thời gian lấy hàng dự kiến.</p>}
        </div>
      </div>
    </div>
  );
}

function Input({ label, value, onChange, placeholder, className = '' }: { label: string; value: string; onChange: (v: string) => void; placeholder?: string; className?: string }) {
  return (
    <div className={className}>
      <div className="text-[12.5px] font-medium text-ink-400 mb-1">{label}</div>
      <input value={value} onChange={(e) => onChange(e.target.value)} placeholder={placeholder} className="w-full h-11 rounded-xl border border-slate-300 px-3 text-[14px] outline-none focus:border-accent-500" />
    </div>
  );
}
