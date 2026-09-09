import { useState } from 'react';
import { ArrowLeftRight, Languages, Copy } from 'lucide-react';
import PageHeader from '../components/ui/PageHeader';
import Card from '../components/ui/Card';
import Button from '../components/ui/Button';
import { useToast } from '../lib/dataContext';

const DICTIONARY: Record<string, string> = {
  'xin chào': '你好',
  'hóa đơn': '发票',
  'phiếu đóng gói': '装箱单',
  'hợp đồng': '合同',
  'thông quan': '清关',
  'cửa khẩu': '口岸',
  'lấy hàng': '提货',
  'giao hàng': '交货',
  'thanh toán': '付款',
  'tạm ứng': '预付款',
  'xe tải': '卡车',
  'nhà máy': '工厂',
  'cảm ơn': '谢谢',
  'vui lòng gửi': '请发送',
  'kiểm tra hàng': '验货',
};

const SAMPLES = [
  'Vui lòng gửi hóa đơn và phiếu đóng gói trước khi xe lấy hàng.',
  'Xe tải dự kiến tới nhà máy lúc 8 giờ sáng ngày mai.',
  'Chúng tôi đã thanh toán tạm ứng, vui lòng chuẩn bị thông quan.',
];

export default function Translation() {
  const { push } = useToast();
  const [direction, setDirection] = useState<'vi-zh' | 'zh-vi'>('vi-zh');
  const [input, setInput] = useState('');
  const [output, setOutput] = useState('');

  function translate() {
    if (!input.trim()) return;
    if (direction === 'vi-zh') {
      let result = input;
      Object.entries(DICTIONARY).forEach(([vi, zh]) => {
        result = result.replace(new RegExp(vi, 'gi'), zh);
      });
      setOutput(result === input ? `${input} (chưa có trong từ điển mẫu — bản dịch mô phỏng)` : result);
    } else {
      setOutput(`${input}\n\n(Bản dịch mô phỏng sang Tiếng Việt — vui lòng nhờ đại lý xác nhận lại nội dung quan trọng)`);
    }
    push('Đã dịch nội dung (mô phỏng)', 'success');
  }

  return (
    <div>
      <PageHeader title="Dịch Thuật" subtitle="Công cụ dịch nhanh các cụm từ nghiệp vụ thường dùng khi trao đổi với nhà máy và đại lý Trung Quốc." />

      <Card className="mb-4">
        <div className="flex items-center justify-center gap-4 mb-4">
          <span className={`font-bold text-[14px] ${direction === 'vi-zh' ? 'text-navy-900' : 'text-ink-400'}`}>Tiếng Việt</span>
          <button onClick={() => setDirection((d) => (d === 'vi-zh' ? 'zh-vi' : 'vi-zh'))} className="h-10 w-10 rounded-full bg-slate-100 flex items-center justify-center text-navy-900 hover:bg-slate-200">
            <ArrowLeftRight size={18} />
          </button>
          <span className={`font-bold text-[14px] ${direction === 'zh-vi' ? 'text-navy-900' : 'text-ink-400'}`}>Tiếng Trung</span>
        </div>
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
          <div>
            <div className="text-[12.5px] font-medium text-ink-400 mb-1">{direction === 'vi-zh' ? 'Nhập tiếng Việt' : 'Nhập tiếng Trung'}</div>
            <textarea value={input} onChange={(e) => setInput(e.target.value)} rows={6} placeholder="Nhập nội dung cần dịch..." className="w-full rounded-xl border border-slate-300 px-3.5 py-3 text-[14.5px] outline-none focus:border-accent-500 resize-none" />
            <div className="flex flex-wrap gap-2 mt-2">
              {SAMPLES.map((s) => (
                <button key={s} onClick={() => setInput(s)} className="text-[12px] px-2.5 py-1 rounded-full bg-slate-100 text-ink-600 hover:bg-slate-200">{s.slice(0, 24)}…</button>
              ))}
            </div>
          </div>
          <div>
            <div className="text-[12.5px] font-medium text-ink-400 mb-1">Kết quả</div>
            <div className="w-full min-h-[150px] rounded-xl border border-slate-200 bg-slate-50 px-3.5 py-3 text-[14.5px] whitespace-pre-wrap">{output || '— Bản dịch sẽ hiển thị tại đây —'}</div>
            {output && (
              <button onClick={() => { navigator.clipboard?.writeText(output); push('Đã sao chép bản dịch', 'info'); }} className="mt-2 flex items-center gap-1.5 text-[13px] font-semibold text-accent-600 hover:underline"><Copy size={13} /> Sao chép</button>
            )}
          </div>
        </div>
        <Button size="lg" full icon={<Languages size={18} />} className="mt-4" onClick={translate}>DỊCH NGAY</Button>
      </Card>

      <Card>
        <div className="text-[13px] font-bold text-navy-900 mb-2">Từ điển nghiệp vụ nhanh</div>
        <div className="grid grid-cols-2 sm:grid-cols-3 gap-2">
          {Object.entries(DICTIONARY).map(([vi, zh]) => (
            <div key={vi} className="flex items-center justify-between bg-slate-50 rounded-lg px-3 py-2 text-[13px]">
              <span className="text-ink-900">{vi}</span>
              <span className="text-ink-400 font-mono">{zh}</span>
            </div>
          ))}
        </div>
      </Card>
    </div>
  );
}
