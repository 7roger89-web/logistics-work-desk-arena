import { useNavigate, useParams } from 'react-router-dom';
import { ArrowLeft, Calculator, PackagePlus, FileText, Building2 } from 'lucide-react';
import { useAppData } from '../lib/dataContext';
import { formatVND } from '../lib/mockData';
import Card, { CardTitle, Field } from '../components/ui/Card';
import Button from '../components/ui/Button';
import Badge from '../components/ui/Badge';
import EmptyState from '../components/ui/EmptyState';
import { SHIPMENT_STATUS_LABEL, SHIPMENT_STATUS_VARIANT, QUOTE_STATUS_LABEL, QUOTE_STATUS_VARIANT, CONTRACT_STATUS_LABEL, CONTRACT_STATUS_VARIANT } from '../lib/status';

export default function CustomerDetail() {
  const { id = '' } = useParams();
  const navigate = useNavigate();
  const { customers, shipments, contracts, quotes } = useAppData();
  const customer = customers.find((c) => c.id === id);

  if (!customer) {
    return <Card><EmptyState message={`Không tìm thấy khách hàng "${id}".`} action={<Button onClick={() => navigate('/khach-hang')}>Về danh sách Khách Hàng</Button>} /></Card>;
  }

  const custShipments = shipments.filter((s) => s.customerId === id);
  const custContracts = contracts.filter((c) => c.customerId === id);
  const custQuotes = quotes.filter((q) => q.customerId === id);

  return (
    <div>
      <button onClick={() => navigate('/khach-hang')} className="flex items-center gap-1.5 text-[13.5px] font-semibold text-ink-600 hover:text-navy-900 mb-3"><ArrowLeft size={15} /> Quay lại Khách Hàng</button>

      <Card className="mb-4">
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div>
            <div className="flex items-center gap-2.5 mb-1">
              <Building2 size={20} className="text-accent-500" />
              <h1 className="text-[20px] font-extrabold text-navy-900">{customer.name}</h1>
            </div>
            <p className="text-[13.5px] text-ink-600">{customer.address}</p>
          </div>
          <div className="flex gap-2 shrink-0">
            <Button variant="secondary" size="sm" icon={<Calculator size={15} />} onClick={() => navigate('/kinh-doanh-bao-gia')}>➕ Tạo báo giá</Button>
            <Button size="sm" icon={<PackagePlus size={15} />} onClick={() => navigate('/tao-lo-moi')}>➕ Tạo lô</Button>
          </div>
        </div>
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 mt-4 pt-4 border-t border-border">
          <Field label="Mã số thuế" value={customer.taxCode} />
          <Field label="Người liên hệ" value={`${customer.contact} · ${customer.phone}`} />
          <Field label="Sale phụ trách" value={customer.sale} />
          <Field label="Công nợ hiện tại" value={customer.debt > 0 ? formatVND(customer.debt) : 'Không nợ'} />
        </div>
        {customer.note && <div className="mt-3 text-[13px] text-ink-600 bg-slate-50 rounded-lg px-3 py-2">📝 {customer.note}</div>}
      </Card>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <Card>
          <div className="flex items-center justify-between mb-3">
            <CardTitle className="mb-0"><Calculator size={17} className="text-accent-500" /> Báo giá</CardTitle>
            <button onClick={() => navigate('/kinh-doanh-bao-gia')} className="text-[13px] font-semibold text-accent-600 hover:underline">Xem tất cả</button>
          </div>
          {custQuotes.length === 0 ? <EmptyState message="Chưa có báo giá nào cho khách hàng này." action={<Button size="sm" onClick={() => navigate('/kinh-doanh-bao-gia')}>➕ Tạo báo giá</Button>} /> : (
            <div className="divide-y divide-border">
              {custQuotes.map((q) => (
                <div key={q.id} className="flex items-center justify-between py-2.5">
                  <div><div className="font-bold text-navy-900 text-[14px]">{q.id}</div><div className="text-[12.5px] text-ink-400">{q.goodsType} · {formatVND(q.sellPrice)}</div></div>
                  <Badge variant={QUOTE_STATUS_VARIANT[q.status]}>{QUOTE_STATUS_LABEL[q.status]}</Badge>
                </div>
              ))}
            </div>
          )}
        </Card>

        <Card>
          <div className="flex items-center justify-between mb-3">
            <CardTitle className="mb-0"><FileText size={17} className="text-accent-500" /> Hợp đồng</CardTitle>
            <button onClick={() => navigate('/hop-dong')} className="text-[13px] font-semibold text-accent-600 hover:underline">Xem hợp đồng</button>
          </div>
          {custContracts.length === 0 ? <EmptyState message="Chưa có hợp đồng nào cho khách hàng này." action={<Button size="sm" onClick={() => navigate('/hop-dong')}>➕ Tạo hợp đồng mới</Button>} /> : (
            <div className="divide-y divide-border">
              {custContracts.map((c) => (
                <button key={c.id} onClick={() => navigate(`/hop-dong/${c.id}`)} className="w-full flex items-center justify-between py-2.5 hover:bg-slate-50 rounded-lg px-1 -mx-1">
                  <div className="text-left"><div className="font-bold text-navy-900 text-[14px]">{c.id}</div><div className="text-[12.5px] text-ink-400">{c.type} · {formatVND(c.value)}</div></div>
                  <Badge variant={CONTRACT_STATUS_VARIANT[c.status]}>{CONTRACT_STATUS_LABEL[c.status]}</Badge>
                </button>
              ))}
            </div>
          )}
        </Card>

        <Card className="lg:col-span-2">
          <CardTitle>Lô hàng</CardTitle>
          {custShipments.length === 0 ? <EmptyState message="Chưa có lô hàng nào cho khách hàng này." action={<Button size="sm" onClick={() => navigate('/tao-lo-moi')}>➕ Tạo lô mới</Button>} /> : (
            <div className="divide-y divide-border">
              {custShipments.map((s) => (
                <button key={s.id} onClick={() => navigate(`/lo-hang/${s.id}`)} className="w-full flex flex-wrap items-center justify-between gap-2 py-2.5 hover:bg-slate-50 rounded-lg px-1 -mx-1 text-left">
                  <div><div className="font-bold text-navy-900 text-[14px]">{s.id}</div><div className="text-[12.5px] text-ink-400">{s.route}</div></div>
                  <Badge variant={SHIPMENT_STATUS_VARIANT[s.status]}>{SHIPMENT_STATUS_LABEL[s.status]}</Badge>
                </button>
              ))}
            </div>
          )}
        </Card>
      </div>
    </div>
  );
}
