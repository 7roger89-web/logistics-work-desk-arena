import { useState } from 'react';
import { Search, ChevronDown, BookOpen } from 'lucide-react';
import PageHeader from '../components/ui/PageHeader';
import Card from '../components/ui/Card';

const SECTIONS = [
  {
    title: 'Pickup & Xuất khẩu',
    tips: [
      'Luôn chốt lịch xe TQ trước tối thiểu 24 giờ với nhà máy để tránh phát sinh phí lưu bãi.',
      'Với hàng cồng kềnh (máy CNC, dây chuyền), yêu cầu nhà máy gửi ảnh đóng gói thực tế trước khi xe tới lấy hàng.',
      'Invoice và Packing List cần khớp số kiện, trọng lượng với thực tế — sai lệch dễ bị giữ hàng tại cửa khẩu.',
    ],
  },
  {
    title: 'Thông quan nhập khẩu',
    tips: [
      'Máy móc đã qua sử dụng cần kiểm tra tuổi thiết bị theo quy định (thường dưới 10 năm) trước khi khai báo.',
      'Chuẩn bị catalogue kỹ thuật + tài liệu chứng minh xuất xứ để rút ngắn thời gian kiểm hoá.',
      'Nếu lô hàng bị phân luồng đỏ, chủ động liên hệ chi cục hải quan để nắm rõ yêu cầu bổ sung sớm nhất.',
    ],
  },
  {
    title: 'Vận chuyển nội địa & Giao hàng',
    tips: [
      'Xác nhận địa chỉ giao hàng chi tiết (số nhà, tên KCN, lô/xưởng) tránh xe phải quay đầu gây phát sinh chi phí.',
      'Luôn chụp ảnh biên bản giao nhận có chữ ký người nhận trước khi rời kho khách.',
      'Với hàng dễ vỡ, yêu cầu tài xế báo cáo tình trạng hàng hoá ngay khi dỡ hàng.',
    ],
  },
  {
    title: 'Chứng từ & Hợp đồng',
    tips: [
      'Tổng giá trị sau VAT từ 50.000.000₫ trở lên bắt buộc dùng HDMB, dưới mức này dùng HDNT + Phụ lục.',
      'Luôn kiểm tra hiệu lực HDNT trước khi tái sử dụng cho phụ lục mới, tránh hợp đồng hết hạn.',
      'Thông tin pháp lý (MST, người đại diện, số tài khoản) cần xác minh với bản sao giấy phép kinh doanh mới nhất.',
    ],
  },
  {
    title: 'Tài Chính & Công Nợ',
    tips: [
      'Không cộng gộp công nợ giữa các đơn vị tiền tệ khác nhau (VND/USD/CNY) trong cùng một dòng báo cáo.',
      'Ghi nhận điều chỉnh giao dịch thay vì xoá — luôn lưu lý do điều chỉnh để phục vụ đối soát cuối kỳ.',
      'Nhắc khách thanh toán trước hạn 2 ngày với các khoản trên 50 triệu để tránh phát sinh nợ quá hạn.',
    ],
  },
];

export default function Handbook() {
  const [query, setQuery] = useState('');
  const [open, setOpen] = useState<string | null>(SECTIONS[0].title);

  const filtered = SECTIONS.map((s) => ({ ...s, tips: s.tips.filter((t) => !query || t.toLowerCase().includes(query.toLowerCase())) })).filter((s) => s.tips.length > 0 || !query);

  return (
    <div>
      <PageHeader title="Sổ Tay Kinh Nghiệm" subtitle="Tổng hợp kinh nghiệm vận hành thực tế giúp nhân viên mới xử lý công việc nhanh và chính xác hơn." />

      <Card className="mb-4">
        <div className="flex items-center gap-2 bg-slate-100 rounded-xl px-3 h-11">
          <Search size={16} className="text-ink-400 shrink-0" />
          <input value={query} onChange={(e) => setQuery(e.target.value)} placeholder="Tìm kinh nghiệm theo từ khoá..." className="bg-transparent flex-1 min-w-0 outline-none text-[14px]" />
        </div>
      </Card>

      <div className="space-y-3">
        {filtered.map((s) => (
          <Card key={s.title} padded={false} className="overflow-hidden">
            <button onClick={() => setOpen(open === s.title ? null : s.title)} className="w-full flex items-center justify-between px-4 sm:px-5 py-4">
              <span className="flex items-center gap-2.5 font-bold text-navy-900 text-[15px]"><BookOpen size={17} className="text-accent-500" /> {s.title}</span>
              <ChevronDown size={18} className={`text-ink-400 transition-transform ${open === s.title ? 'rotate-180' : ''}`} />
            </button>
            {open === s.title && (
              <ul className="px-4 sm:px-5 pb-4 space-y-2.5">
                {s.tips.map((t, i) => (
                  <li key={i} className="flex gap-2.5 text-[14px] text-ink-900 leading-relaxed"><span className="text-accent-500 shrink-0 font-bold">{i + 1}.</span>{t}</li>
                ))}
              </ul>
            )}
          </Card>
        ))}
      </div>
    </div>
  );
}
