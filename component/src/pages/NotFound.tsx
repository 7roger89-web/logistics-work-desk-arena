import { Link } from "react-router-dom";

export default function NotFound() {
  return <section className="rounded-2xl bg-white border border-slate-200 p-6" data-testid="not-found">
    <h1 className="text-xl font-bold">Không tìm thấy màn hình / đường dẫn không hợp lệ</h1>
    <nav className="flex flex-wrap gap-4 mt-4">
      <Link to="/">Tổng Quan</Link>
      <Link to="/hop-dong">Hợp đồng</Link>
      <Link to="/lo-hang">Lô Hàng</Link>
    </nav>
  </section>;
}
