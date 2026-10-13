import {useEffect,useState} from 'react';
import {Building2,Users,CarFront,GitBranch,ShieldCheck,RefreshCw} from 'lucide-react';
import {api} from '../services/api';
import {useI18n} from '../i18n';

export function Enterprise(){
 const {t}=useI18n(); const [data,setData]=useState<any>(null); const [loading,setLoading]=useState(true); const [error,setError]=useState('');
 const load=()=>{setLoading(true);api.enterpriseControlPlane().then(setData).catch(e=>setError(e.message)).finally(()=>setLoading(false));}; useEffect(load,[]);
 if(loading)return <div className="loading-screen"><span className="spinner"/>{t('Yuklanmoqda...')}</div>;
 if(error)return <div className="page"><div className="notice error">{error}</div><button className="btn" onClick={load}><RefreshCw size={14}/>{t('Yangilash')}</button></div>;
 const o=data.organization;
 return <div className="page company-center">
  <div className="page-head"><div><p className="eyebrow">V56 · ENTERPRISE CONTROL PLANE</p><h1>{o.name}</h1><p>{o.code} · {t('Tashkilot boshqaruvi, filiallar, tariflar va foydalanish limitlari')}</p></div><button className="btn" onClick={load}><RefreshCw size={14}/>{t('Yangilash')}</button></div>
  <div className="stat-grid"><div className="stat"><Building2/><span>{t('Kompaniyalar')}</span><strong>{data.summary.active_companies}</strong><small>{o.max_companies} {t('limit')}</small></div><div className="stat"><GitBranch/><span>{t('Filiallar')}</span><strong>{data.summary.branches}</strong></div><div className="stat"><Users/><span>{t('Foydalanuvchilar')}</span><strong>{data.summary.users}</strong></div><div className="stat"><CarFront/><span>{t('Avtomobillar')}</span><strong>{data.summary.vehicles}</strong></div></div>
  <div className="panel"><div className="panel-head"><div><h2>{t('Kompaniyalar')}</h2><p>{t('Har bir kompaniya bo‘yicha tenant, filial va tarif holati')}</p></div><ShieldCheck size={20}/></div><div className="members-table"><table><thead><tr><th>{t('Kompaniya')}</th><th>{t('Tarif')}</th><th>{t('Foydalanuvchilar')}</th><th>{t('Avtomobillar')}</th><th>{t('Filiallar')}</th><th>{t('Holat')}</th></tr></thead><tbody>{data.companies.map((c:any)=><tr key={c.id}><td><strong>{c.name}</strong><small>{c.code}</small></td><td><span className="badge">{c.plan||'—'}</span><small>{c.subscription_status||'—'}</small></td><td>{c.users} / {c.user_limit}</td><td>{c.vehicles} / {c.vehicle_limit}</td><td>{c.branches}</td><td><span className={`badge ${c.is_active?'ok':'danger'}`}>{c.is_active?t('Faol'):t('Nofaol')}</span></td></tr>)}</tbody></table></div></div>
  <div className="panel"><div className="panel-head"><div><h2>{t('Tariflar')}</h2><p>{t('Mavjud SaaS tariflari va asosiy limitlar')}</p></div></div><div className="company-grid">{data.plans.map((p:any)=><div className="panel company-stat-card" key={p.id}><span>{p.name}</span><strong>{Number(p.price_monthly).toLocaleString()} UZS</strong><small>{p.user_limit} {t('foydalanuvchi')} · {p.vehicle_limit} {t('avtomobil')}</small></div>)}</div></div>
 </div>
}
