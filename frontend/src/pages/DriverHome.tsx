import {useEffect,useState} from 'react';
import {Camera,MapPin,Navigation,AlertTriangle,Clock3,CheckCircle2,ChevronRight,Route,PhoneCall,RefreshCw,Truck} from 'lucide-react';
import {api} from '../services/api';

export function DriverHome(){
 const [data,setData]=useState<any>(null); const [loading,setLoading]=useState(true); const [error,setError]=useState('');
 const load=()=>{setLoading(true);api.dashboard().then(setData).catch(e=>setError(e instanceof Error?e.message:'Ma’lumot yuklanmadi')).finally(()=>setLoading(false))};
 useEffect(()=>{load()},[]);
 const trip=data?.recent_trips?.[0];
 return <main className="driver-home page">
  <section className="driver-welcome"><div><span className="driver-overline">AVTOPARK PRO · HAYDOVCHI</span><h1>Yo‘lingiz bexatar bo‘lsin!</h1><p>Bugungi reys va topshiriqlaringiz shu yerda.</p></div><button className="driver-refresh" onClick={load} aria-label="Yangilash"><RefreshCw size={18}/></button></section>
  {error&&<div className="alert error">{error}</div>}
  <section className="driver-map-card"><div className="driver-map-image"/><div className="driver-map-top"><span className="driver-live"><i/> REYS HOLATI</span><span className="driver-map-date"><Clock3 size={13}/>{new Date().toLocaleDateString('uz-UZ',{day:'2-digit',month:'short'})}</span></div><div className="driver-route-summary"><div className="driver-route-icon"><Navigation size={21}/></div><div><small>JORIY TOPSHIRIQ</small><strong>{loading?'Yuklanmoqda…':trip?.route||'Faol reys belgilanmagan'}</strong><span>{trip?`${trip.vehicle} · ${trip.driver}`:'Yangi reys tayinlanganda shu yerda ko‘rinadi'}</span></div><span className="driver-route-chevron"><ChevronRight size={19}/></span></div><div className="driver-route-line"><span/><div><b>{trip?.route?.split('→')?.[0]?.trim()||'Boshlanish nuqtasi'}</b><small>Jo‘nash manzili</small></div><div><b>{trip?.route?.split('→')?.[1]?.trim()||'Belgilangan manzil'}</b><small>Yetib borish nuqtasi</small></div></div><a className="driver-open-trip" href="/trips"><Route size={17}/> Reys tafsilotlari <ChevronRight size={16}/></a></section>
  <section className="driver-quick-grid"><a className="driver-action fuel" href="/fuel"><span><Camera size={25}/></span><strong>Yoqilg‘i chekini yuklash</strong><small>Foto va OCR tekshiruvi</small><i><ChevronRight size={17}/></i></a><a className="driver-action issue" href="/maintenance"><span><AlertTriangle size={25}/></span><strong>Nosozlik haqida xabar</strong><small>Transport holatini bildirish</small><i><ChevronRight size={17}/></i></a></section>
  <section className="driver-status-card"><div className="driver-status-icon"><Truck size={19}/></div><div><strong>Bugungi faoliyat</strong><span>{data?.today_trips??0} reys · {data?.today_done??0} yakunlangan</span></div><div className="driver-status-badge"><CheckCircle2 size={14}/> Kuzatuvda</div></section>
  <section className="driver-help"><PhoneCall size={16}/><div><strong>Yordam kerakmi?</strong><span>Dispetcher bilan bog‘lanish uchun Chat bo‘limidan foydalaning.</span></div><a href="/chat">Chat <ChevronRight size={15}/></a></section>
  <nav className="driver-bottom-nav"><a className="selected" href="/"><Truck size={18}/><span>Bosh sahifa</span></a><a href="/trips"><Route size={18}/><span>Reyslar</span></a><a href="/fuel"><Camera size={18}/><span>Yoqilg‘i</span></a><a href="/chat"><PhoneCall size={18}/><span>Aloqa</span></a></nav>
 </main>
}
