import {useEffect,useMemo,useState} from "react";
import {Download,Search,Wrench} from "lucide-react";
import {api} from "../services/api";

type Row={id:number;date:string;part_id:number;part:any;vehicle_id:number;vehicle:string;driver_id:number|null;driver:string;maintenance_id:number|null;maintenance:string;odometer:number;quantity:number;unit_price:number;total:number;service_type:string;note:string};
type Data={results:Row[];summary:{count:number;quantity:number;total:number};meta:{vehicles:{id:number;number:string;model:string;mileage:number}[]}};
const money=(n:number)=>new Intl.NumberFormat("uz-UZ",{maximumFractionDigits:2}).format(n);
const num=(n:number)=>new Intl.NumberFormat("uz-UZ",{maximumFractionDigits:1}).format(n);
export function Replacements(){
 const[data,setData]=useState<Data|null>(null);const[loading,setLoading]=useState(true);const[vehicle,setVehicle]=useState("");const[q,setQ]=useState("");
 const load=()=>{setLoading(true);api.replacements(vehicle,q).then(setData).finally(()=>setLoading(false))};useEffect(load,[vehicle,q]);
 const rows=useMemo(()=>data?.results||[],[data]);
 if(loading&&!data)return <div className="loading-screen"><span className="spinner"/>Almashtirishlar tarixi yuklanmoqda...</div>;
 return <div className="page"><div className="page-head"><div><p className="eyebrow">SERVIS · TARIX</p><h1>Almashtirishlar tarixi</h1><p>Har bir avtomobilga chiqarilgan ehtiyot qismlar, probeg va real xarajatlar.</p></div><div className="actions"><button className="btn" onClick={()=>window.location.href="/avtomobillar/"}><Wrench size={15}/> Avtomobil profili</button></div></div>
 <div className="maintenance-stats"><div className="stat"><span>Operatsiyalar</span><strong>{data?.summary.count||0}</strong></div><div className="stat"><span>Jami miqdor</span><strong>{num(data?.summary.quantity||0)}</strong></div><div className="stat"><span>Jami xarajat</span><strong>{money(data?.summary.total||0)} so‘m</strong></div></div>
 <div className="fuel-toolbar"><div style={{display:"flex",alignItems:"center",gap:8}}><Search size={16}/><input placeholder="Detal yoki servis bo‘yicha qidirish" value={q} onChange={e=>setQ(e.target.value)} /></div><select value={vehicle} onChange={e=>setVehicle(e.target.value)}><option value="">Barcha avtomobillar</option>{data?.meta.vehicles.map(v=><option key={v.id} value={v.id}>{v.number} · {v.model}</option>)}</select><button className="btn" onClick={()=>window.location.href=`/api/v1/replacements/export/?vehicle=${encodeURIComponent(vehicle)}`}><Download size={15}/> Excel nakladnoy</button></div>
 <div className="table-wrap maintenance-table"><table><thead><tr><th>Sana</th><th>Avtomobil</th><th>Ehtiyot qism</th><th>Servis</th><th>Probeg</th><th>Miqdor</th><th>Birlik narxi</th><th>Jami</th><th>Izoh</th></tr></thead><tbody>{rows.map(x=><tr key={x.id}><td>{x.date}</td><td><strong>{x.vehicle}</strong><small>{x.driver||"Haydovchi ko‘rsatilmagan"}</small></td><td><strong>{x.part?.name}</strong><small>{x.part?.code}</small></td><td>{x.service_type||x.maintenance||"—"}</td><td>{num(x.odometer)} km</td><td>{num(x.quantity)} {x.part?.unit||""}</td><td>{money(x.unit_price)}</td><td><strong>{money(x.total)} so‘m</strong></td><td>{x.note||"—"}</td></tr>)}</tbody></table>{!rows.length&&<div className="empty">Almashtirish tarixi topilmadi.</div>}</div></div>
}
