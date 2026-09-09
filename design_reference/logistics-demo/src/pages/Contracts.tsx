import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Plus, Search, FolderOpen } from 'lucide-react';
import { useAppData } from '../lib/dataContext';
import { AGENTS, formatMoney } from '../lib/mockData';
import PageHeader from '../components/ui/PageHeader';
import Card from '../components/ui/Card';
import Badge from '../components/ui/Badge';
import Button from '../components/ui/Button';
import Modal from '../components/ui/Modal';
import EmptyState from '../components/ui/EmptyState';
import { CONTRACT_STATUS_LABEL, CONTRACT_STATUS_VARIANT } from '../lib/status';
import type { ContractType } from '../lib/types';

export default function Contracts() {
  const navigate = useNavigate();
  const { contracts, customers, addContract } = useAppData();
  const [query, setQuery] = useState('');
  const [type, setType] = useState('ALL');
  const [status, setStatus] = useState('ALL');
  const [agent, setAgent] = useState('ALL');

  const [createOpen, setCreateOpen] = useState(false);
  const [newType, setNewType] = useState<ContractType>('HDMB');
  const [newAgent, setNewAgent] = useState(AGENTS[0]);
  const [newCustomerId, setNewCustomerId] = useState('');

  const filtered = contracts.filter((c) => {
    if (type !== 'ALL' && c.type !== type) return false;
    if (status !== 'ALL' && c.status !== status) return false;
    if (agent !== 'ALL' && c.agent !== agent) return false;
    if (query) {
      const q = query.toLowerCase();
      if (!`${c.id} ${c.agent} ${c.company}`.toLowerCase().includes(q)) return false;
    }
    return true;
  });

  function handleCreate() {
    const customer = customers.find((c) => c.id === newCustomerId);
    if (!customer) return;
    const id = addContract({ type: newType, agent: newAgent, company: customer.name, customerId: customer.id });
    setCreateOpen(false);
    navigate(`/hop-dong/${id}`);
  }

  return (
    <div>
      <PageHeader
        title="Hợp Đồng"
        subtitle="Bàn làm việc chính cho toàn bộ hợp đồng nguyên tắc, phụ lục và hợp đồng mua bán."
        actions={<Button icon={<Plus size={17} />} onClick={() => setCreateOpen(true)}>➕ TẠO HỢP ĐỒNG MỚI</Button>}
      />

      <Card className="mb-4 space-y-3">
        <div className="flex items-center gap-2 bg-slate-100 rounded-xl px-3 h-11">
          <Search size={16} className="text-ink-400 shrink-0" />
          <input value={query} onChange={(e) => setQuery(e.target.value)} placeholder="Tìm theo số hợp đồng, đại lý, công ty..." className="bg-transparent flex-1 min-w-0 outline-none text-[14px]" />
        </div>
        <div className="flex flex-wrap gap-2">
          {[['ALL', 'Tất cả loại'], ['HDMB', 'HDMB'], ['HDNT', 'HDNT']].map(([v, l]) => (
            <button key={v} onClick={() => setType(v)} className={`px-3.5 h-9 rounded-lg text-[13px] font-semibold border ${type === v ? 'bg-navy-900 text-white border-navy-900' : 'bg-white text-ink-600 border-slate-300'}`}>{l}</button>
          ))}
          <span className="w-px bg-border mx-1" />
          {[['ALL', 'Tất cả trạng thái'], ['DRAFT', 'Nháp'], ['DA_PHAT_HANH', 'Đã phát hành']].map(([v, l]) => (
            <button key={v} onClick={() => setStatus(v)} className={`px-3.5 h-9 rounded-lg text-[13px] font-semibold border ${status === v ? 'bg-navy-900 text-white border-navy-900' : 'bg-white text-ink-600 border-slate-300'}`}>{l}</button>
          ))}
          <select value={agent} onChange={(e) => setAgent(e.target.value)} className="h-9 rounded-lg border border-slate-300 px-2.5 text-[13px]">
            <option value="ALL">Tất cả đại lý</option>
            {AGENTS.map((a) => <option key={a} value={a}>{a}</option>)}
          </select>
        </div>
      </Card>

      {filtered.length === 0 ? (
        <Card><EmptyState message="Chưa có hợp đồng nào khớp bộ lọc." action={<Button onClick={() => setCreateOpen(true)}>➕ TẠO HỢP ĐỒNG MỚI</Button>} /></Card>
      ) : (
        <>
          <Card padded={false} className="hidden lg:block overflow-hidden">
            <table className="w-full text-left border-collapse">
              <thead>
                <tr className="bg-slate-50 text-[12px] text-ink-400 font-bold uppercase tracking-wide">
                  <th className="px-4 py-3">Số hợp đồng</th>
                  <th className="px-4 py-3">Loại</th>
                  <th className="px-4 py-3">Đại lý</th>
                  <th className="px-4 py-3">Công ty</th>
                  <th className="px-4 py-3">Giá trị</th>
                  <th className="px-4 py-3">Hiệu lực</th>
                  <th className="px-4 py-3">Số lô</th>
                  <th className="px-4 py-3">Trạng thái</th>
                  <th className="px-4 py-3">Hành động</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border">
                {filtered.map((c) => (
                  <tr key={c.id} className="hover:bg-slate-50">
                    <td className="px-4 py-3.5 font-bold text-navy-900 whitespace-nowrap">{c.id}</td>
                    <td className="px-4 py-3.5"><Badge variant="neutral" icon={false}>{c.type}</Badge></td>
                    <td className="px-4 py-3.5 text-[13px] text-ink-600 max-w-[160px] truncate">{c.agent}</td>
                    <td className="px-4 py-3.5 text-[13px] text-ink-600 max-w-[180px] truncate">{c.company}</td>
                    <td className="px-4 py-3.5 text-[13.5px] font-semibold text-navy-900 whitespace-nowrap">{c.value ? formatMoney(c.value, 'VND') : '—'}</td>
                    <td className="px-4 py-3.5 text-[12.5px] text-ink-400 whitespace-nowrap">{c.validFrom ? `${c.validFrom} - ${c.validTo}` : 'Chưa xác định'}</td>
                    <td className="px-4 py-3.5 text-[13.5px] text-ink-600 text-center">{c.linkedShipmentIds.length}</td>
                    <td className="px-4 py-3.5"><Badge variant={CONTRACT_STATUS_VARIANT[c.status]}>{CONTRACT_STATUS_LABEL[c.status]}</Badge></td>
                    <td className="px-4 py-3.5"><Button size="sm" icon={<FolderOpen size={14} />} onClick={() => navigate(`/hop-dong/${c.id}`)}>MỞ HỢP ĐỒNG</Button></td>
                  </tr>
                ))}
              </tbody>
            </table>
          </Card>

          <div className="lg:hidden space-y-3">
            {filtered.map((c) => (
              <Card key={c.id} className="space-y-2">
                <div className="flex items-center justify-between">
                  <span className="font-extrabold text-navy-900 text-[15px]">{c.id}</span>
                  <Badge variant={CONTRACT_STATUS_VARIANT[c.status]}>{CONTRACT_STATUS_LABEL[c.status]}</Badge>
                </div>
                <div className="text-[13.5px] text-ink-900 font-semibold">{c.company}</div>
                <div className="text-[13px] text-ink-600">Đại lý: {c.agent}</div>
                <div className="flex items-center justify-between text-[12.5px] text-ink-400 pt-1 border-t border-border">
                  <span>{c.type} · {c.linkedShipmentIds.length} lô</span>
                  <span>{c.value ? formatMoney(c.value, 'VND') : '—'}</span>
                </div>
                <Button full onClick={() => navigate(`/hop-dong/${c.id}`)}>MỞ HỢP ĐỒNG</Button>
              </Card>
            ))}
          </div>
        </>
      )}

      <Modal open={createOpen} onClose={() => setCreateOpen(false)} title="Tạo hợp đồng mới">
        <div className="space-y-4">
          <div>
            <div className="text-[12.5px] font-medium text-ink-400 mb-1">Loại hợp đồng *</div>
            <div className="grid grid-cols-2 gap-3">
              <button onClick={() => setNewType('HDNT')} className={`h-11 rounded-xl font-bold text-[14px] border ${newType === 'HDNT' ? 'bg-navy-900 text-white border-navy-900' : 'bg-white text-ink-600 border-slate-300'}`}>HDNT (+ Phụ lục)</button>
              <button onClick={() => setNewType('HDMB')} className={`h-11 rounded-xl font-bold text-[14px] border ${newType === 'HDMB' ? 'bg-navy-900 text-white border-navy-900' : 'bg-white text-ink-600 border-slate-300'}`}>HDMB</button>
            </div>
          </div>
          <div>
            <div className="text-[12.5px] font-medium text-ink-400 mb-1">Đại lý (Bên bán) *</div>
            <select value={newAgent} onChange={(e) => setNewAgent(e.target.value)} className="w-full h-11 rounded-xl border border-slate-300 px-3 text-[14px]">
              {AGENTS.map((a) => <option key={a} value={a}>{a}</option>)}
            </select>
          </div>
          <div>
            <div className="text-[12.5px] font-medium text-ink-400 mb-1">Công ty / Khách hàng (Bên mua) *</div>
            <select value={newCustomerId} onChange={(e) => setNewCustomerId(e.target.value)} className="w-full h-11 rounded-xl border border-slate-300 px-3 text-[14px]">
              <option value="">— Chọn khách hàng —</option>
              {customers.map((c) => <option key={c.id} value={c.id}>{c.name}</option>)}
            </select>
          </div>
          <Button full disabled={!newCustomerId} onClick={handleCreate}>✅ Tạo hợp đồng nháp</Button>
        </div>
      </Modal>
    </div>
  );
}
