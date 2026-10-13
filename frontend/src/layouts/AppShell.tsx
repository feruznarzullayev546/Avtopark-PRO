import React, { useEffect, useState } from "react";
import { NavLink } from "react-router-dom";
import {
  LayoutDashboard, CarFront, Route, Users, Package, Fuel, Bell,
  Wrench, Wallet, Menu, X, LogOut, Building2, ChevronDown, Plus,
  Check, ShieldCheck, Globe2, MapPin, CreditCard, Shield, Settings,
  MessageCircle, FileBarChart
} from "lucide-react";
import { api } from "../services/api";
import type { Me } from "../types/api";
import { useI18n } from "../i18n";

const items = [
  ["/", "Boshqaruv paneli", LayoutDashboard],
  ["/vehicles", "Avtomobillar", CarFront],
  ["/trips", "Reyslar", Route],
  ["/routes", "Yo‘nalishlar", Route],
  ["/drivers", "Haydovchilar", Users],
  ["/warehouse", "Sklad", Package],
  ["/fuel", "Yoqilg'i", Fuel],
  ["/finance", "Xarajatlar", Wallet],
  ["/reports", "Hisobotlar", FileBarChart],
  ["/chat", "Chat", MessageCircle],
  ["/settings", "Profil / Sozlamalar", Settings],
  ["/maintenance", "Servis", Wrench],
  ["/notifications", "Bildirishnomalar", Bell],
  ["/companies", "Kompaniya boshqaruvi", Building2],
  ["/access", "Security & RBAC", ShieldCheck],
  ["/enterprise", "Enterprise Control Plane", Globe2],
  ["/billing", "Billing & Subscription", CreditCard],
  ["/platform", "Platform Control Center", Shield]
] as const;

export function AppShell({ children, me, onLogout }: { children: React.ReactNode; me: Me; onLogout: () => void }) {
  const { lang, setLang, t } = useI18n();
  const [open, setOpen] = useState(false);
  const [navSearch, setNavSearch] = useState('');
  const [avatarUrl, setAvatarUrl] = useState<string | null>(me.user?.avatar_url || null);
  const [companies, setCompanies] = useState<any[]>([]);
  const [branches, setBranches] = useState<any[]>([]);
  const [activeBranch, setActiveBranch] = useState<any>(null);
  const [companyMenu, setCompanyMenu] = useState(false);
  const [createOpen, setCreateOpen] = useState(false);
  const [newCompany, setNewCompany] = useState({ name: '', industry: '', tin: '' });

  useEffect(() => {
    if (!open) return;
    const previousOverflow = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    const onKeyDown = (event: KeyboardEvent) => {
      if (event.key === "Escape") setOpen(false);
    };
    window.addEventListener("keydown", onKeyDown);
    return () => {
      document.body.style.overflow = previousOverflow;
      window.removeEventListener("keydown", onKeyDown);
    };
  }, [open]);

  useEffect(() => {
    setAvatarUrl(me.user?.avatar_url || null);
    const syncAvatar = (e: Event) => setAvatarUrl((e as CustomEvent).detail?.avatar_url ?? null);
    window.addEventListener("avtopark:avatar", syncAvatar);
    return () => window.removeEventListener("avtopark:avatar", syncAvatar);
  }, [me.user?.avatar_url]);

  useEffect(() => {
    api.companyContext().then(r => setCompanies(r.companies || [])).catch(() => {});
    api.enterpriseContext().then(r => {
      setBranches(r.branches || []);
      const saved = localStorage.getItem('avtopark_active_branch_id');
      const b = (r.branches || []).find((x: any) => String(x.id) === saved) || r.active_branch;
      if (b) {
        setActiveBranch(b);
        localStorage.setItem('avtopark_active_branch_id', String(b.id));
      }
    }).catch(() => {});
  }, [me.company?.id]);

  const active = companies.find(c => c.id === me.company?.id);
  const logout = async () => { await api.logout(); onLogout(); };

  const switchCompany = async (id: number) => {
    if (id === me.company?.id) return;
    localStorage.removeItem('avtopark_active_branch_id');
    await api.switchCompany(id);
    window.location.reload();
  };

  const switchBranch = async (id: number) => {
    if (!id) return;
    await api.switchBranch(id);
    localStorage.setItem('avtopark_active_branch_id', String(id));
    setActiveBranch(branches.find(b => b.id === id) || null);
    setCompanyMenu(false);
    window.location.reload();
  };

  const createCompany = async () => {
    if (!newCompany.name.trim()) return;
    await api.createCompany(newCompany);
    window.location.reload();
  };

  const formattedDate = new Intl.DateTimeFormat(
    lang === 'ru' ? 'ru-RU' : 'uz-Latn-UZ',
    { weekday: 'short', day: '2-digit', month: 'short', year: 'numeric' }
  ).format(new Date());

  return (
    <div className="shell">
      <button className="mobile-menu" type="button" onClick={() => setOpen(true)} aria-label="Menyuni ochish" aria-expanded={open} aria-controls="avtopark-sidebar"><Menu size={21} /></button>
      {open && <button className="overlay" type="button" onClick={() => setOpen(false)} aria-label="Menyuni yopish" /> }

      <aside id="avtopark-sidebar" aria-hidden={!open && typeof window !== "undefined" && window.matchMedia("(max-width: 760px)").matches} className={`sidebar role-${(me.user?.role || "viewer").toLowerCase()} ${open ? "is-open" : ""}`}>
        <div className="brand">
          <span className="brand-mark">AP</span>
          <div className="brand-copy">
            <strong>AVTOPARK <em>PRO</em></strong>
            <small>Fleet Management System</small>
          </div>
          <button className="close-menu" onClick={() => setOpen(false)} aria-label="Menyuni yopish"><X size={18} /></button>
        </div>

        <div className="lang-switcher">
          <button className={lang === 'uz' ? 'active' : ''} onClick={() => setLang('uz')}>UZ</button>
          <button className={lang === 'ru' ? 'active' : ''} onClick={() => setLang('ru')}>RU</button>
        </div>

        <div className="company-switcher">
          <button className="company-switcher-btn" onClick={() => setCompanyMenu(v => !v)}>
            <span className="company-switch-icon"><Building2 size={15} /></span>
            <span>
              <b>{active?.name || me.company?.name || 'Kompaniya'}</b>
              <small>{active?.code || me.company?.code || 'ACTIVE TENANT'}{activeBranch?.name ? ` · ${activeBranch.name}` : ''}</small>
            </span>
            <ChevronDown size={14} />
          </button>

          {companyMenu && (
            <div className="company-menu">
              {companies.map(c => (
                <button key={c.id} className={c.id === me.company?.id ? 'selected' : ''} onClick={() => switchCompany(c.id)}>
                  <span><b>{c.name}</b><small>{c.code} · {c.role}</small></span>
                  {c.id === me.company?.id && <Check size={14} />}
                </button>
              ))}
              <div className="company-menu-divider" />
              <div style={{ padding: '8px 10px 4px', fontSize: 11, fontWeight: 800, color: '#718096', textTransform: 'uppercase' }}>
                {t('Faol filial')}
              </div>
              <select value={activeBranch?.id || ''} onChange={e => switchBranch(Number(e.target.value))} style={{ margin: '0 10px 10px', width: 'calc(100% - 20px)' }}>
                {branches.filter(b => b.company_id === me.company?.id).map((b: any) => (
                  <option key={b.id} value={b.id}>{b.name} · {b.code}</option>
                ))}
              </select>
              <div className="company-menu-divider" />
              <button className="company-create-btn" onClick={() => setCreateOpen(true)}><Plus size={14} /> {t('Yangi kompaniya')}</button>
            </div>
          )}
        </div>

        {/* SKROLL BO'LADIGAN MENYU VA AKKAUNT BLOKI */}
        <nav className="sidebar-nav">
          {items.filter(([to, label]) => {
            const role = me.user?.role || "";
            if (to === "/platform" && !me.is_super) return false;
            if ((to === "/companies" || to === "/access" || to === "/enterprise") && !me.is_super && !["DIRECTOR", "MANAGER"].includes(role)) return false;
            if (to === "/chat" && !me.is_super && !["DIRECTOR", "MANAGER", "DRIVER"].includes(role)) return false;
            if (role === "DRIVER" && !["/", "/trips", "/fuel", "/chat", "/settings"].includes(to)) return false;
            if (["ACCOUNTANT", "WAREHOUSE", "VIEWER"].includes(role) && to === "/platform") return false;
            return !navSearch.trim() || label.toLowerCase().includes(navSearch.trim().toLowerCase()) || to.toLowerCase().includes(navSearch.trim().toLowerCase());
          }).map(([to, label, Icon]) => (
            <NavLink key={to} to={to} end={to === "/"} onClick={() => setOpen(false)} className={({ isActive }) => isActive ? "nav-item active" : "nav-item"}>
              <Icon size={18} />
              <span>{t(label)}</span>
            </NavLink>
          ))}

          {/* AKKAUNT BLOKI (SKROLL OXIRIDA CHIQADI, QOTIB TURMAYDI) */}
          <div className="user-box inline-user-box">
            <div className="avatar">
              {avatarUrl ? <img src={avatarUrl} alt="" /> : (me.user?.full_name || "U").slice(0, 1).toUpperCase()}
            </div>
            <div className="user-info">
              <strong>{me.user?.full_name || me.user?.username}</strong>
              <span>{me.user?.role || "Foydalanuvchi"}</span>
            </div>
            <button className="logout" onClick={logout} title={t('Chiqish')}><LogOut size={16} /></button>
          </div>
        </nav>
      </aside>

      <main className="content">
        <header className="app-topbar">
          <div className="topbar-context">
            <span className="topbar-date-icon"><Globe2 size={17} /></span>
            <div>
              <strong>{formattedDate}</strong>
              <small><MapPin size={11} style={{ display: 'inline', verticalAlign: '-2px', marginRight: 4 }} />Toshkent (UTC+5){activeBranch?.name ? ` · ${activeBranch.name}` : ''}</small>
            </div>
          </div>
          <label className="topbar-search">
            <span>⌕</span>
            <input value={navSearch} onChange={e => setNavSearch(e.target.value)} placeholder={t('Bo‘lim qidirish…')} aria-label="Menyudan bo‘lim qidirish" />
            <kbd>MENU</kbd>
          </label>
          <div className="topbar-actions">
            <NavLink to="/notifications" className="topbar-icon" title={t('Bildirishnomalar')} aria-label={t('Bildirishnomalar')}>
              <Bell size={18} />
              <span className="notification-dot" aria-hidden="true" />
            </NavLink>
            <div className="topbar-user">
              <span className="topbar-avatar">{avatarUrl ? <img src={avatarUrl} alt="" /> : (me.user?.full_name || me.user?.username || 'U').slice(0, 1).toUpperCase()}</span>
              <span><strong>{me.user?.full_name || me.user?.username}</strong><small>{me.user?.role || 'Foydalanuvchi'}</small></span>
            </div>
          </div>
        </header>

        <div className="content-inner">{children}</div>
      </main>

      {createOpen && (
        <div className="modal-backdrop" onMouseDown={() => setCreateOpen(false)}>
          <div className="modal company-create-modal" onMouseDown={e => e.stopPropagation()}>
            <div className="modal-head">
              <div>
                <h2>{t('Yangi kompaniya')}</h2>
                <p>{t('Yangi tenant va direktor membership avtomatik yaratiladi.')}</p>
              </div>
              <button onClick={() => setCreateOpen(false)}>×</button>
            </div>
            <div className="form-grid">
              <label>{t('Kompaniya nomi')}<input value={newCompany.name} onChange={e => setNewCompany({ ...newCompany, name: e.target.value })} /></label>
              <label>{t('Faoliyat sohasi')}<input value={newCompany.industry} onChange={e => setNewCompany({ ...newCompany, industry: e.target.value })} /></label>
              <label>{t('STIR')}<input value={newCompany.tin} onChange={e => setNewCompany({ ...newCompany, tin: e.target.value })} /></label>
            </div>
            <div className="modal-actions">
              <button className="btn" onClick={() => setCreateOpen(false)}>{t('Bekor qilish')}</button>
              <button className="btn primary" onClick={createCompany}><Plus size={14} /> {t('Yaratish')}</button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}