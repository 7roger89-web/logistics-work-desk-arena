import { useState } from 'react';
import { UserPlus, Lock, Unlock, ShieldAlert } from 'lucide-react';
import { useAppData, useRole } from '../lib/dataContext';
import PageHeader from '../components/ui/PageHeader';
import Card from '../components/ui/Card';
import Badge from '../components/ui/Badge';
import Button from '../components/ui/Button';
import Modal from '../components/ui/Modal';
import type { Role } from '../lib/types';

const ROLE_LABEL: Record<Role, string> = { ADMIN: 'Quản trị viên', SUPPORT: 'Nhân viên vận hành', SALE: 'Nhân viên kinh doanh' };

export default function UsersPage() {
  const { role } = useRole();
  const { users, toggleUserLock, addUser } = useAppData();
  const [createOpen, setCreateOpen] = useState(false);
  const [name, setName] = useState('');
  const [username, setUsername] = useState('');
  const [newRole, setNewRole] = useState<Role>('SUPPORT');

  function handleCreate() {
    if (!name || !username) return;
    addUser({ name, username, role: newRole });
    setName(''); setUsername(''); setNewRole('SUPPORT');
    setCreateOpen(false);
  }

  return (
    <div>
      <PageHeader
        title="Người Dùng"
        subtitle="Quản trị tài khoản nhân viên và phân quyền truy cập hệ thống."
        actions={<Button icon={<UserPlus size={17} />} onClick={() => setCreateOpen(true)} disabled={role !== 'ADMIN'}>➕ Tạo người dùng</Button>}
      />

      {role !== 'ADMIN' && (
        <div className="mb-4 flex items-center gap-3 bg-warning-50 border border-warning-500/30 rounded-xl p-3.5 text-[13.5px] text-warning-600 font-semibold">
          <ShieldAlert size={18} className="shrink-0" /> Bạn đang xem với quyền hạn chế. Chuyển vai trò sang "Quản trị viên" ở góc trên bên phải để thao tác đầy đủ.
        </div>
      )}

      <Card padded={false} className="hidden lg:block overflow-hidden">
        <table className="w-full text-left border-collapse">
          <thead>
            <tr className="bg-slate-50 text-[12px] text-ink-400 font-bold uppercase tracking-wide">
              <th className="px-4 py-3">Họ tên</th>
              <th className="px-4 py-3">Tên đăng nhập</th>
              <th className="px-4 py-3">Vai trò</th>
              <th className="px-4 py-3">Trạng thái</th>
              <th className="px-4 py-3">Đăng nhập gần nhất</th>
              <th className="px-4 py-3">Hành động</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-border">
            {users.map((u) => (
              <tr key={u.id} className="hover:bg-slate-50">
                <td className="px-4 py-3.5 font-bold text-navy-900 whitespace-nowrap">{u.name}</td>
                <td className="px-4 py-3.5 text-[13.5px] text-ink-600 font-mono">{u.username}</td>
                <td className="px-4 py-3.5"><Badge variant="info" icon={false}>{ROLE_LABEL[u.role]}</Badge></td>
                <td className="px-4 py-3.5">{u.status === 'ACTIVE' ? <Badge variant="success">Hoạt động</Badge> : <Badge variant="danger">Đã khoá</Badge>}</td>
                <td className="px-4 py-3.5 text-[12.5px] text-ink-400 whitespace-nowrap">{u.lastLogin}</td>
                <td className="px-4 py-3.5">
                  <Button size="sm" variant={u.status === 'ACTIVE' ? 'danger' : 'success'} disabled={role !== 'ADMIN'} icon={u.status === 'ACTIVE' ? <Lock size={13} /> : <Unlock size={13} />} onClick={() => toggleUserLock(u.id)}>
                    {u.status === 'ACTIVE' ? 'Khoá' : 'Mở khoá'}
                  </Button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </Card>

      <div className="lg:hidden space-y-3">
        {users.map((u) => (
          <Card key={u.id} className="space-y-2">
            <div className="flex items-center justify-between">
              <span className="font-bold text-navy-900 text-[15px]">{u.name}</span>
              {u.status === 'ACTIVE' ? <Badge variant="success">Hoạt động</Badge> : <Badge variant="danger">Đã khoá</Badge>}
            </div>
            <div className="text-[13px] text-ink-600 font-mono">@{u.username}</div>
            <div className="flex items-center justify-between pt-1 border-t border-border">
              <Badge variant="info" icon={false}>{ROLE_LABEL[u.role]}</Badge>
              <span className="text-[12px] text-ink-400">{u.lastLogin}</span>
            </div>
            <Button full variant={u.status === 'ACTIVE' ? 'danger' : 'success'} disabled={role !== 'ADMIN'} onClick={() => toggleUserLock(u.id)}>
              {u.status === 'ACTIVE' ? 'Khoá tài khoản' : 'Mở khoá tài khoản'}
            </Button>
          </Card>
        ))}
      </div>

      <Modal open={createOpen} onClose={() => setCreateOpen(false)} title="Tạo người dùng mới">
        <div className="space-y-4">
          <div>
            <div className="text-[12.5px] font-medium text-ink-400 mb-1">Họ tên *</div>
            <input value={name} onChange={(e) => setName(e.target.value)} className="w-full h-11 rounded-xl border border-slate-300 px-3 text-[14px]" />
          </div>
          <div>
            <div className="text-[12.5px] font-medium text-ink-400 mb-1">Tên đăng nhập *</div>
            <input value={username} onChange={(e) => setUsername(e.target.value)} className="w-full h-11 rounded-xl border border-slate-300 px-3 text-[14px]" />
          </div>
          <div>
            <div className="text-[12.5px] font-medium text-ink-400 mb-1">Vai trò</div>
            <select value={newRole} onChange={(e) => setNewRole(e.target.value as Role)} className="w-full h-11 rounded-xl border border-slate-300 px-3 text-[14px]">
              <option value="ADMIN">Quản trị viên</option>
              <option value="SUPPORT">Nhân viên vận hành</option>
              <option value="SALE">Nhân viên kinh doanh</option>
            </select>
          </div>
          <Button full disabled={!name || !username} onClick={handleCreate}>✅ Tạo người dùng</Button>
        </div>
      </Modal>
    </div>
  );
}
