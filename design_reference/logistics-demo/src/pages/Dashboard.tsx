import { useNavigate } from 'react-router-dom';
import {
  Truck, FileWarning, PackageCheck, CircleDollarSign, FileX2,
  ChevronRight, PlayCircle, Clock, ArrowRightCircle, Ship, ClipboardCheck, CheckCircle2, Wallet, HandCoins, AlertTriangle,
} from 'lucide-react';
import { useAppData, useRole } from '../lib/dataContext';
import { TASKS, formatVND } from '../lib/mockData';
import Card from '../components/ui/Card';
import StatCard from '../components/ui/StatCard';
import Badge from '../components/ui/Badge';
import Button from '../components/ui/Button';
import { PRIORITY_LABEL, PRIORITY_VARIANT } from '../lib/status';

export default function Dashboard() {
  const navigate = useNavigate();
  const { userName } = useRole();
  const { shipments } = useAppData();

  const choLayHang = shipments.filter((s) => s.status === 'CHO_LAY_HANG');
  const dangVanChuyen = shipments.filter((s) => s.status === 'DANG_VAN_CHUYEN');
  const choThongQuan = shipments.filter((s) => s.status === 'CHO_THONG_QUAN');
  const choGiao = shipments.filter((s) => s.status === 'CHO_GIAO');
  const daGiao = shipments.filter((s) => s.status === 'DA_GIAO');
  const thieuChungTu = shipments.filter((s) => s.checklist.some((c) => c.status !== 'DU'));
  const canThu = shipments.filter((s) => s.finance.receivable.total - s.finance.receivable.paid > 0);
  const tongPhaiThu = shipments.reduce((sum, s) => sum + Math.max(0, s.finance.receivable.total - s.finance.receivable.paid), 0);
  const tongPhaiTra = shipments.reduce((sum, s) => sum + Math.max(0, s.finance.payable.total - s.finance.payable.paid), 0);
  const quaHan = TASKS.filter((t) => t.status.includes('Quá hạn'));

  const nextActionCards = [
    { label: 'Lô cần lấy hàng', count: choLayHang.length, icon: <Truck size={18} />, tone: 'info' as const, filter: 'CHO_LAY_HANG' },
    { label: 'Lô cần thông quan', count: choThongQuan.length, icon: <FileWarning size={18} />, tone: 'warning' as const, filter: 'CHO_THONG_QUAN' },
    { label: 'Lô cần giao', count: choGiao.length, icon: <PackageCheck size={18} />, tone: 'warning' as const, filter: 'CHO_GIAO' },
    { label: 'Khoản cần thu', count: canThu.length, sub: formatVND(tongPhaiThu), icon: <CircleDollarSign size={18} />, tone: 'danger' as const, filter: '' , financeLink: true},
    { label: 'Hồ sơ thiếu chứng từ', count: thieuChungTu.length, icon: <FileX2 size={18} />, tone: 'danger' as const, filter: 'THIEU_HS' },
  ];

  const urgentTasks = [...TASKS].sort((a, b) => (a.priority === 'KHAN' ? -1 : 1)).slice(0, 5);

  return (
    <div>
      <div className="mb-5">
        <h1 className="text-[22px] sm:text-[26px] font-extrabold text-navy-900 tracking-tight">Chào buổi sáng, {userName.split(' ').slice(-2).join(' ')} 👋</h1>
        <p className="text-[14.5px] text-ink-600 mt-1">Hôm nay là Thứ Ba, 08/09/2026 · Câu hỏi quan trọng nhất: <span className="font-semibold text-navy-900">"Hôm nay tôi cần làm gì?"</span></p>
      </div>

      <div className="mb-6">
        <div className="flex items-center justify-between mb-3">
          <h2 className="text-[15px] font-bold text-navy-900 flex items-center gap-2"><PlayCircle size={17} className="text-accent-500" /> VIỆC TIẾP THEO</h2>
        </div>
        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-3">
          {nextActionCards.map((c) => (
            <StatCard
              key={c.label}
              label={c.label}
              value={c.count}
              sub={c.sub}
              icon={c.icon}
              tone={c.tone}
              onClick={() => {
                if (c.financeLink) navigate('/thu-tien-cong-no');
                else if (c.filter === 'THIEU_HS') navigate('/lo-hang?docs=thieu');
                else navigate(`/lo-hang?status=${c.filter}`);
              }}
            />
          ))}
        </div>
      </div>

      <div className="grid grid-cols-1 xl:grid-cols-3 gap-4 mb-6">
        <div className="xl:col-span-2">
          <div className="flex items-center justify-between mb-3">
            <h2 className="text-[15px] font-bold text-navy-900 flex items-center gap-2"><ClipboardCheck size={17} className="text-accent-500" /> VIỆC CẦN XỬ LÝ HÔM NAY</h2>
            <button onClick={() => navigate('/viec-can-xu-ly')} className="text-[13px] font-semibold text-accent-600 flex items-center gap-0.5 hover:underline">Xem tất cả <ChevronRight size={14} /></button>
          </div>
          <Card padded={false} className="divide-y divide-border overflow-hidden">
            {urgentTasks.map((t) => (
              <button
                key={t.id}
                onClick={() => navigate(`/lo-hang/${t.shipmentId}?tab=${t.tab}`)}
                className="w-full text-left flex items-center gap-3 px-4 py-3.5 hover:bg-slate-50 transition-colors"
              >
                <Badge variant={PRIORITY_VARIANT[t.priority]} className="shrink-0">{PRIORITY_LABEL[t.priority]}</Badge>
                <div className="min-w-0 flex-1">
                  <div className="text-[14px] font-semibold text-navy-900 truncate">{t.action}</div>
                  <div className="text-[12.5px] text-ink-400 truncate">{t.shipmentId} · {t.customer} · Hạn {t.due}</div>
                </div>
                <ArrowRightCircle size={19} className="text-ink-400 shrink-0" />
              </button>
            ))}
          </Card>
        </div>
        <div>
          <div className="flex items-center justify-between mb-3">
            <h2 className="text-[15px] font-bold text-navy-900 flex items-center gap-2"><Ship size={17} className="text-accent-500" /> LỐI TẮT</h2>
          </div>
          <Card className="space-y-2.5">
            <Button full variant="primary" onClick={() => navigate('/tao-lo-moi')}>➕ Tạo lô mới</Button>
            <Button full variant="secondary" onClick={() => navigate('/kinh-doanh-bao-gia')}>➕ Tạo báo giá</Button>
            <Button full variant="secondary" onClick={() => navigate('/hop-dong')}>➕ Tạo hợp đồng mới</Button>
          </Card>
        </div>
      </div>

      <div>
        <h2 className="text-[15px] font-bold text-navy-900 mb-3">CHỈ SỐ VẬN HÀNH</h2>
        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-3">
          <StatCard label="Lô đang chạy" value={shipments.filter((s) => s.status !== 'DA_GIAO').length} icon={<Truck size={16} />} tone="neutral" onClick={() => navigate('/lo-hang')} />
          <StatCard label="Chờ lấy hàng" value={choLayHang.length} icon={<Clock size={16} />} tone="neutral" onClick={() => navigate('/lo-hang?status=CHO_LAY_HANG')} />
          <StatCard label="Đang vận chuyển" value={dangVanChuyen.length} icon={<Truck size={16} />} tone="info" onClick={() => navigate('/lo-hang?status=DANG_VAN_CHUYEN')} />
          <StatCard label="Chờ thông quan" value={choThongQuan.length} icon={<FileWarning size={16} />} tone="warning" onClick={() => navigate('/lo-hang?status=CHO_THONG_QUAN')} />
          <StatCard label="Chờ giao" value={choGiao.length} icon={<PackageCheck size={16} />} tone="warning" onClick={() => navigate('/lo-hang?status=CHO_GIAO')} />
          <StatCard label="Đã giao hôm nay" value={daGiao.length} icon={<CheckCircle2 size={16} />} tone="success" onClick={() => navigate('/lo-hang?status=DA_GIAO')} />
          <StatCard label="Phải thu" value={formatVND(tongPhaiThu)} icon={<Wallet size={16} />} tone="danger" onClick={() => navigate('/thu-tien-cong-no')} />
          <StatCard label="Phải trả" value={formatVND(tongPhaiTra)} icon={<HandCoins size={16} />} tone="warning" onClick={() => navigate('/cong-no-doi-tac')} />
          <StatCard label="Việc quá hạn" value={quaHan.length} icon={<AlertTriangle size={16} />} tone="danger" onClick={() => navigate('/viec-can-xu-ly')} />
        </div>
      </div>
    </div>
  );
}
