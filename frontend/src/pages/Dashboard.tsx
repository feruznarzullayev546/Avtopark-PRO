import {useCallback, useEffect, useMemo, useState} from "react";
import type {CSSProperties, ReactNode} from "react";
import {Activity, AlertTriangle, Bell, Boxes, CarFront, CheckCircle2, ChevronRight, Fuel, Gauge, RefreshCw, Route as RouteIcon, ShieldCheck, Truck, Users, Wrench, Zap} from "lucide-react";
import {api} from "../services/api";
import { ThemeToggle } from "../components/ui/ThemeToggle";

export type DashboardData = {
  company:{id:number;name:string;code:string;status:string;trial_ends_at:string|null};
  subscription:{plan:string;plan_code:string;status:string;period_end:string|null;trial_days_left:number|null}|null;
  vehicles:number;drivers:number;routes:number;trips:number;today_trips:number;today_done:number;today_active:number;
  month_trips:number;month_done:number;month_cancelled:number;month_fuel:number;month_issues:number;month_expenses:number;done_km:number;cost_per_km:number;
  unread_notifications:number;low_stock_count:number;service_alert_count:number;
  low_stock:{id:number;code:string;name:string;stock:number;min_stock:number}[];
  service_alerts:{id:number;vehicle:string;part:string;status:string;remaining_km:number;remaining_days:number}[];
  recent_trips:{id:number;trip_no:number;date:string;status:string;route:string;vehicle:string;driver:string;km:number}[];
};

const money=(n:number)=>new Intl.NumberFormat("uz-UZ",{maximumFractionDigits:0}).format(n);
const num=(n:number)=>new Intl.NumberFormat("uz-UZ",{maximumFractionDigits:1}).format(n);
const statusLabel=(s:string)=>({PLANNED:"Rejalashtirilgan",CONFIRMED:"Tasdiqlangan",DONE:"Bajarilgan",CANCELLED:"Bekor qilingan"}[s]||s);

function MiniChart({done,cancelled}:{done:number;cancelled:number}){
  const total=Math.max(done+cancelled,1); const donePct=Math.round(done/total*100);
  return <div className="donut" style={{"--done":`${donePct}%`} as CSSProperties}><div><strong>{donePct}%</strong><span>bajarilgan</span></div></div>;
}

export function Dashboard(){
  const [data,setData]=useState<DashboardData|null>(null); const [error,setError]=useState(""); const [loading,setLoading]=useState(true);
  const loadDashboard = useCallback(() => {
    setLoading(true); setError("");
    api.dashboard().then(setData).catch(e=>setError(e instanceof Error?e.message:"API xatosi")).finally(()=>setLoading(false));
  },[]);
  useEffect(()=>{loadDashboard();},[loadDashboard]);
  const date=useMemo(()=>new Intl.DateTimeFormat("uz-UZ",{weekday:"long",day:"2-digit",month:"long"}).format(new Date()),[]);
  if(loading) return <section className="dashboard-page"><div className="dashboard-skeleton"><div/><div/><div/><div/></div></section>;
  if(error||!data) return <section className="dashboard-page"><div className="dashboard-error"><AlertTriangle/><div><strong>Dashboard yuklanmadi</strong><p>{error||"Ma’lumot topilmadi"}</p></div><button className="btn primary" onClick={()=>window.location.reload()}>Qayta yuklash</button></div></section>;
  const trial=data.subscription?.status==="TRIAL";
  return <section className="dashboard-page">
    <div className="dashboard-hero">
      <div><div className="eyebrow">{date.toUpperCase()}</div><h1 >Xush kelibsiz 👋</h1><p><strong>{data.company.name}</strong> — bugungi operatsion holat bir oynada.</p></div>
      <div className="hero-actions"><ThemeToggle/><div className="live-pill"><span/> LIVE DATA</div><button className="icon-action" title="Ma’lumotlarni yangilash" aria-label="Ma’lumotlarni yangilash" onClick={loadDashboard}><RefreshCw size={17}/></button><a className="icon-action notification-action" href="/notifications" title="Bildirishnomalar" aria-label="Bildirishnomalar"><Bell size={18}/>{data.unread_notifications>0&&<b>{data.unread_notifications}</b>}</a></div>
    </div>

    {trial&&<div className="trial-banner"><div className="trial-icon"><Zap size={19}/></div><div><strong>START Free Trial faol</strong><span>{data.subscription?.trial_days_left===0?"Sinov muddati bugun tugaydi.":`${data.subscription?.trial_days_left} kun bepul foydalanish qoldi.`} Barcha imkoniyatlarni sinab ko‘ring.</span></div><a className="btn primary" href="/billing">Tariflarni ko‘rish <ChevronRight size={15}/></a></div>}

    <div className="dashboard-kpis">
      <Kpi icon={<CarFront/>} label="Faol avtomobillar" value={data.vehicles} meta="Hozir faol holatdagi transport" tone="blue" />
      <Kpi icon={<Fuel/>} label="Yoqilg‘i xarajati" value={money(data.month_fuel)} meta="Joriy oy · so‘m" tone="orange" />
      <Kpi icon={<RouteIcon/>} label="Bajarilgan reyslar" value={data.month_done} meta={`${data.month_trips} ta reysdan · joriy oy`} tone="green" />
      <Kpi icon={<Gauge/>} label="Umumiy xarajat" value={money(data.month_expenses)} meta="Yoqilg‘i + sklad · joriy oy, so‘m" tone="violet" />
    </div>

    <div className="dashboard-analytics-grid">
      <div className="analytics-card trip-analytics-card">
        <div className="analytics-head"><div><span className="eyebrow">FAOLIYAT TAHLILI</span><h2>So‘nggi reyslar masofasi</h2><p>Dashboardga kelgan oxirgi reyslar bo‘yicha, km</p></div><span className="analytics-chip"><Activity size={13}/> {data.recent_trips.length} ta reys</span></div>
        <TripDistanceChart trips={data.recent_trips}/>
      </div>
      <div className="analytics-card completion-card">
        <div className="analytics-head"><div><span className="eyebrow">OYLIK NATIJA</span><h2>Reyslar holati</h2><p>Joriy oy bo‘yicha</p></div><RouteIcon size={18} className="analytics-head-icon"/></div>
        <div className="completion-number"><strong>{data.month_trips.toLocaleString("uz-UZ")}</strong><span>jami reys</span></div>
        <div className="status-meter"><span className="status-done" style={{width:`${data.month_trips?Math.min(100,data.month_done/data.month_trips*100):0}%`}}/><span className="status-cancelled" style={{width:`${data.month_trips?Math.min(100,data.month_cancelled/data.month_trips*100):0}%`}}/></div>
        <div className="status-legend"><span><i className="legend-green"/> Bajarilgan <strong>{data.month_done}</strong></span><span><i className="legend-red"/> Bekor qilingan <strong>{data.month_cancelled}</strong></span></div>
        <div className="completion-footer"><span>Bajarilish darajasi</span><strong>{data.month_trips?Math.round(data.month_done/data.month_trips*100):0}%</strong></div>
      </div>
    </div>

    <div className="dashboard-main-grid">
      <div className="dashboard-left">
        <div className="section-heading"><div><span className="eyebrow">OPERATSION NAZORAT</span><h2>Bugungi park</h2></div><span className="soft-badge"><Activity size={13}/> Jonli</span></div>
        <div className="operation-card">
          <div className="operation-summary"><div className="operation-icon"><Truck size={22}/></div><div><strong>{data.today_active}</strong><span>Faol reys</span></div><div className="operation-divider"/><div><strong>{data.today_done}</strong><span>Yakunlangan</span></div><div className="operation-divider"/><div><strong>{data.month_done}</strong><span>Oy bo‘yicha</span></div><MiniChart done={data.month_done} cancelled={data.month_cancelled}/></div>
          <div className="progress-line"><span style={{width:`${Math.min(100, data.today_trips ? data.today_done/data.today_trips*100 : 0)}%`}}/></div>
          <div className="progress-meta"><span>Bugungi bajarilish</span><strong>{data.today_trips?Math.round(data.today_done/data.today_trips*100):0}%</strong></div>
        </div>

        <div className="section-heading spaced"><div><span className="eyebrow">SO‘NGGI OPERATSIYALAR</span><h2>Reyslar jurnali</h2></div><a href="/trips">Barchasini ko‘rish <ChevronRight size={14}/></a></div>
        <div className="dashboard-table-card"><div className="dashboard-table-scroll"><table><thead><tr><th>Reys</th><th>Yo‘nalish</th><th>Transport</th><th>Haydovchi</th><th>Holat</th><th>Masofa</th></tr></thead><tbody>{data.recent_trips.length?data.recent_trips.map(t=><tr key={t.id}><td><strong>#{t.trip_no}</strong><small>{t.date}</small></td><td><strong>{t.route}</strong></td><td>{t.vehicle}</td><td>{t.driver}</td><td><span className={`trip-status ${t.status.toLowerCase()}`}><i/>{statusLabel(t.status)}</span></td><td>{num(t.km)} km</td></tr>):<tr><td colSpan={6}><div className="empty">Hozircha reyslar mavjud emas.</div></td></tr>}</tbody></table></div></div>
      </div>

      <aside className="dashboard-right">
        <div className="side-card finance-card"><div className="side-card-head"><div><span className="eyebrow">OYLIK MOLIYA</span><h3>Xarajatlar</h3></div><div className="side-icon"><Gauge size={17}/></div></div><strong className="big-money">{money(data.month_expenses)} <small>so‘m</small></strong><div className="expense-visual" aria-label="Oylik xarajatlar tarkibi"><div className="expense-stack"><span className="fuel-segment" style={{width:`${data.month_expenses>0?Math.min(100,data.month_fuel/data.month_expenses*100):0}%`}}/><span className="warehouse-segment" style={{width:`${data.month_expenses>0?Math.min(100,data.month_issues/data.month_expenses*100):0}%`}}/><span className="other-segment" style={{width:`${data.month_expenses>0?Math.max(0,100-Math.min(100,(data.month_fuel+data.month_issues)/data.month_expenses*100)):0}%`}}/></div><div className="expense-legend"><span><i className="fuel-dot"/>Yoqilg‘i</span><span><i className="warehouse-dot"/>Ombor</span><span><i className="other-dot"/>Boshqa</span></div></div><div className="finance-rows"><div><span><Fuel size={13}/> Yoqilg‘i</span><strong>{money(data.month_fuel)}</strong></div><div><span><Boxes size={13}/> Ombor</span><strong>{money(data.month_issues)}</strong></div><div><span><Gauge size={13}/> 1 km tannarx</span><strong>{money(data.cost_per_km)} so‘m</strong></div></div></div>

        <div className="side-card alert-card"><div className="side-card-head"><div><span className="eyebrow">DIQQAT</span><h3>Tezkor ogohlantirishlar</h3></div><AlertTriangle size={17}/></div>{data.low_stock_count===0&&data.service_alert_count===0?<div className="all-good"><CheckCircle2 size={22}/><div><strong>Hammasi joyida</strong><span>Hozircha kritik ogohlantirish yo‘q.</span></div></div>:<div className="alert-list">{data.service_alerts.slice(0,3).map(a=><div className="alert-row" key={`s${a.id}`}><div className="alert-dot orange"><Wrench size={13}/></div><div><strong>{a.vehicle} · {a.part}</strong><span>{a.remaining_days<=0?"Servis muddati o‘tgan":`${a.remaining_days} kun / ${num(a.remaining_km)} km qoldi`}</span></div></div>)}{data.low_stock.slice(0,3).map(a=><div className="alert-row" key={`p${a.id}`}><div className="alert-dot red"><Boxes size={13}/></div><div><strong>{a.name}</strong><span>Qoldiq {num(a.stock)} · minimum {num(a.min_stock)}</span></div></div>)}</div>}</div>

        <div className="side-card plan-mini"><div className="side-card-head"><div><span className="eyebrow">ACCOUNT</span><h3>Joriy tarif</h3></div><ShieldCheck size={17}/></div><div className="plan-mini-main"><div className="plan-avatar">{data.subscription?.plan_code?.slice(0,2).toUpperCase()||"ST"}</div><div><strong>{data.subscription?.plan||"START"}</strong><span>{trial?`${data.subscription?.trial_days_left} kun trial`:data.subscription?.status||"—"}</span></div><ChevronRight size={16}/></div></div>
      </aside>
    </div>
  </section>;
}

function Kpi({icon,label,value,meta,tone,alert}:{icon:ReactNode;label:string;value:number|string;meta:string;tone:string;alert?:boolean}){return <div className={`dashboard-kpi ${tone} ${alert?"is-alert":""}`}><div className="kpi-top"><span className="kpi-icon">{icon}</span><span className="kpi-trend">{alert?<AlertTriangle size={14}/>:<Activity size={14}/>}</span></div><strong>{typeof value==="number"?value.toLocaleString("uz-UZ"):value}</strong><span className="kpi-label">{label}</span><small>{meta}</small></div>}


function TripDistanceChart({trips}:{trips:DashboardData["recent_trips"]}){
  const grouped = useMemo(()=>{
    const map = new Map<string,{label:string;km:number;count:number}>();
    trips.forEach(t=>{
      const key=t.date || "—";
      const item=map.get(key)||{label:key,km:0,count:0};
      item.km += Number(t.km)||0; item.count += 1; map.set(key,item);
    });
    return Array.from(map.values()).slice(0,8).reverse();
  },[trips]);
  if(!grouped.length) return <div className="chart-empty">Reyslar kiritilgach, masofa grafigi shu yerda ko‘rinadi.</div>;
  const max=Math.max(...grouped.map(x=>x.km),1);
  const points=grouped.map((x,i)=>`${grouped.length===1?50:i*100/(grouped.length-1)},${92-(x.km/max)*70}`).join(" ");
  return <div className="distance-chart-wrap">
    <div className="distance-chart-y"><span>{num(max)} km</span><span>{num(max/2)} km</span><span>0 km</span></div>
    <svg className="distance-chart" viewBox="0 0 100 100" preserveAspectRatio="none" role="img" aria-label="So‘nggi reyslar bo‘yicha masofa grafigi">
      <defs><linearGradient id="distanceFill" x1="0" y1="0" x2="0" y2="1"><stop offset="0%" stopColor="#3b82f6" stopOpacity=".22"/><stop offset="100%" stopColor="#3b82f6" stopOpacity="0"/></linearGradient></defs>
      {[22,57,92].map(y=><line key={y} x1="0" x2="100" y1={y} y2={y} stroke="#e9eef6" strokeDasharray="2 2" vectorEffect="non-scaling-stroke"/>)}
      <polygon points={`0,92 ${points} 100,92`} fill="url(#distanceFill)"/>
      <polyline points={points} fill="none" stroke="#3478f6" strokeWidth="2.2" vectorEffect="non-scaling-stroke" strokeLinecap="round" strokeLinejoin="round"/>
      {grouped.map((x,i)=><circle key={`${x.label}-${i}`} cx={grouped.length===1?50:i*100/(grouped.length-1)} cy={92-(x.km/max)*70} r="2.1" fill="#fff" stroke="#3478f6" strokeWidth="1.5" vectorEffect="non-scaling-stroke"><title>{x.label}: {num(x.km)} km · {x.count} reys</title></circle>)}
    </svg>
    <div className="distance-chart-labels">{grouped.map((x,i)=><span key={`${x.label}-${i}`} title={`${x.label}: ${num(x.km)} km`}>{x.label.slice(0,5)}</span>)}</div>
  </div>;
}
