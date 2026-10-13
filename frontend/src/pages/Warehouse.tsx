import {useEffect, useMemo, useState} from "react";
import {
  Package, Plus, Search, Pencil, ArrowDownToLine, ArrowUpFromLine, AlertTriangle,
  RefreshCw, RotateCcw, ClipboardCheck, History, Boxes, TrendingUp, TrendingDown,
  Eye, X, Filter, Download, ChevronRight, Truck, Wrench, CircleDollarSign
} from "lucide-react";
import {api} from "../services/api";

type Part={id:number;code:string;name:string;category:string;model:string;unit:string;min_stock:number;unit_price:number;stock:number;stock_value:number;status:"LOW"|"OK"|"CRITICAL"};
type Receipt={id:number;date:string;part_id:number;part:Part;compatible_model:string;quantity:number;unit_price:number;total:number;supplier:string;document_no:string;note:string};
type Issue={id:number;date:string;part_id:number;part:Part;vehicle_id:number;vehicle:string;driver_id:number|null;driver:string;maintenance_id:number|null;maintenance:string;odometer:number;quantity:number;unit_price:number;total:number;service_type:string;note:string};
type ReturnRow={id:number;date:string;issue_id:number;part_id:number;part:Part;vehicle_id:number;vehicle:string;quantity:number;unit_price:number;total:number;document_no:string;reason:string;note:string};
type Adjustment={id:number;date:string;part_id:number;part:Part;quantity:number;unit_price:number;total:number;reason:string;document_no:string;note:string;type:"SURPLUS"|"SHORTAGE"};
type Meta={vehicles:{id:number;number:string;model:string;mileage:number}[];drivers:{id:number;name:string;vehicle_id:number|null;vehicle:string}[];maintenance:{id:number;name:string;vehicle_id:number;vehicle:string;part_id:number|null}[]};

const money=(n:number)=>new Intl.NumberFormat("uz-UZ",{maximumFractionDigits:0}).format(n)+" so‘m";
const num=(n:number)=>new Intl.NumberFormat("uz-UZ",{maximumFractionDigits:2}).format(n);
const today=()=>new Date().toISOString().slice(0,10);

type Tab="overview"|"stock"|"receipts"|"issues"|"returns"|"inventory";
const tabs:[Tab,string][]=[["overview","Dashboard"],["stock","Qoldiq"],["receipts","Kirim"],["issues","Chiqim"],["returns","Qaytarish"],["inventory","Inventarizatsiya"]];

export function Warehouse(){
 const [data,setData]=useState<{parts:Part[];receipts:Receipt[];issues:Issue[];returns:ReturnRow[];adjustments:Adjustment[];summary:any;meta:Meta}>({
   parts:[],receipts:[],issues:[],returns:[],adjustments:[],summary:{},meta:{vehicles:[],drivers:[],maintenance:[]}
 });
 const [tab,setTab]=useState<Tab>("overview");
 const [query,setQuery]=useState(""); const [busy,setBusy]=useState(true); const [error,setError]=useState("");
 const [modal,setModal]=useState<"part"|"receipt"|"issue"|"return"|"adjustment"|"card"|null>(null);
 const [editing,setEditing]=useState<any>(null);
 const [category,setCategory]=useState("all");
 const [status,setStatus]=useState("all");

 const load=async()=>{setBusy(true);setError("");try{setData(await api.warehouse());}catch(e){setError(e instanceof Error?e.message:"Sklad yuklanmadi");}finally{setBusy(false)}};
 useEffect(()=>{load()},[]);

 const filteredParts=useMemo(()=>data.parts.filter(p=>{
   const q=`${p.code} ${p.name} ${p.category} ${p.model}`.toLowerCase();
   return q.includes(query.toLowerCase()) && (category==="all"||p.category===category) && (status==="all"||p.status===status);
 }),[data.parts,query,category,status]);
 const receipts=useMemo(()=>data.receipts.filter(r=>`${r.part.name} ${r.part.code} ${r.supplier} ${r.document_no}`.toLowerCase().includes(query.toLowerCase())),[data.receipts,query]);
 const issues=useMemo(()=>data.issues.filter(r=>`${r.part.name} ${r.part.code} ${r.vehicle} ${r.driver}`.toLowerCase().includes(query.toLowerCase())),[data.issues,query]);
 const returns=useMemo(()=>data.returns.filter(r=>`${r.part.name} ${r.part.code} ${r.vehicle} ${r.reason}`.toLowerCase().includes(query.toLowerCase())),[data.returns,query]);
 const adjustments=useMemo(()=>data.adjustments.filter(r=>`${r.part.name} ${r.part.code} ${r.reason} ${r.document_no}`.toLowerCase().includes(query.toLowerCase())),[data.adjustments,query]);
 const categories=useMemo(()=>Array.from(new Set(data.parts.map(p=>p.category).filter(Boolean))),[data.parts]);
 const low=useMemo(()=>data.parts.filter(p=>p.status!=="OK").sort((a,b)=>a.stock-b.stock),[data.parts]);
 const top=useMemo(()=>[...data.issues].sort((a,b)=>b.total-a.total).slice(0,6),[data.issues]);

 const close=()=>{setModal(null);setEditing(null)};
 const saved=async()=>{close();await load()};
 const openCreate=()=>{setEditing(null);setModal(tab==="stock"?"part":tab==="receipts"?"receipt":tab==="issues"?"issue":tab==="returns"?"return":tab==="inventory"?"adjustment":"part")};

 return <div className="page warehouse-pro">
  <div className="warehouse-hero warehouse-hero-reference">
   <div className="warehouse-hero-copy">
    <div className="eyebrow">OMBOR • REAL-TIME CONTROL</div>
    <h1>Sklad / Ombor</h1>
    <p>Ehtiyot qismlar, materiallar va ularning harakatini bitta professional markazdan boshqaring.</p>
   </div>
   <div className="warehouse-hero-actions">
    <button className="btn ghost-light" onClick={load}><RefreshCw size={14}/> Yangilash</button>
    <button className="btn primary" onClick={openCreate}><Plus size={15}/> {tab==="stock"?"Mahsulot":tab==="receipts"?"Kirim":tab==="issues"?"Chiqim":tab==="returns"?"Qaytarish":tab==="inventory"?"Inventarizatsiya":"Yangi operatsiya"}</button>
   </div>
  </div>

  {error&&<div className="alert danger">{error}</div>}

  <div className="warehouse-kpis">
   <Kpi icon={<Boxes/>} label="Jami mahsulot" value={num(data.summary.items||0)} meta={`${data.summary.low||0} ta nazorat talab qiladi`} tone="blue"/>
   <Kpi icon={<CircleDollarSign/>} label="Ombor qiymati" value={money(data.summary.value||0)} meta="weighted-average tannarx" tone="green"/>
   <Kpi icon={<TrendingUp/>} label="Jami kirim" value={money(data.summary.receipts_total||0)} meta={`${data.receipts.length} ta hujjat`} tone="violet"/>
   <Kpi icon={<TrendingDown/>} label="Jami chiqim" value={money(data.summary.issues_total||0)} meta={`${data.issues.length} ta operatsiya`} tone="orange"/>
   <Kpi icon={<AlertTriangle/>} label="Kritik qoldiq" value={String(data.summary.low||0)} meta="minimal limitdan past" tone="red"/>
  </div>

  <div className="warehouse-nav">
   {tabs.map(([key,label])=><button key={key} className={tab===key?"active":""} onClick={()=>setTab(key)}>
     {key==="overview"?<Boxes size={15}/>:key==="stock"?<Package size={15}/>:key==="receipts"?<ArrowDownToLine size={15}/>:key==="issues"?<ArrowUpFromLine size={15}/>:key==="returns"?<RotateCcw size={15}/>:<ClipboardCheck size={15}/>}
     {label}
   </button>)}
  </div>

  {tab==="overview"?<Overview data={data} low={low} top={top} onPart={p=>{setEditing(p);setModal("card")}}/>:
   <>
    <div className="warehouse-toolbar">
      <div className="smart-search"><Search size={16}/><input value={query} onChange={e=>setQuery(e.target.value)} placeholder="Kod, mahsulot, avtomobil, yetkazib beruvchi yoki hujjat..."/></div>
      {(tab==="stock")&&<><div className="select-wrap"><Filter size={14}/><select value={category} onChange={e=>setCategory(e.target.value)}><option value="all">Barcha kategoriyalar</option>{categories.map(c=><option key={c}>{c}</option>)}</select></div><div className="select-wrap"><select value={status} onChange={e=>setStatus(e.target.value)}><option value="all">Barcha holat</option><option value="OK">Yetarli</option><option value="LOW">Kam</option><option value="CRITICAL">Kritik</option></select></div></>}
      <button className="btn export-btn" onClick={()=>window.open(api.warehouseExport(),"_blank")}><Download size={14}/> Excel / CSV</button>
    </div>
    {busy?<div className="empty"><span className="spinner"/></div>:
      tab==="stock"?<StockTable rows={filteredParts} onEdit={p=>{setEditing(p);setModal("part")}} onCard={p=>{setEditing(p);setModal("card")}}/>:
      tab==="receipts"?<ReceiptTable rows={receipts} onEdit={r=>{setEditing(r);setModal("receipt")}}/>:
      tab==="issues"?<IssueTable rows={issues} onEdit={i=>{setEditing(i);setModal("issue")}}/>:
      tab==="returns"?<ReturnTable rows={returns}/>:
      <AdjustmentTable rows={adjustments}/>}
   </>
  }

  {modal==="part"&&<PartModal item={editing} onClose={close} onSaved={saved}/>}
  {modal==="receipt"&&<ReceiptModal item={editing} parts={data.parts} onClose={close} onSaved={saved}/>}
  {modal==="issue"&&<IssueModal item={editing} parts={data.parts} meta={data.meta} onClose={close} onSaved={saved}/>}
  {modal==="return"&&<ReturnModal issues={data.issues} onClose={close} onSaved={saved}/>}
  {modal==="adjustment"&&<AdjustmentModal parts={data.parts} onClose={close} onSaved={saved}/>}
  {modal==="card"&&<CardModal part={editing} onClose={close}/>}
 </div>
}

function Kpi({icon,label,value,meta,tone}:{icon:React.ReactNode;label:string;value:string;meta:string;tone:string}){
 return <div className={`warehouse-kpi ${tone}`}><div className="kpi-icon">{icon}</div><div><span>{label}</span><strong>{value}</strong><small>{meta}</small></div><ChevronRight size={16} className="kpi-arrow"/></div>
}

function Overview({data,low,top,onPart}:{data:any;low:Part[];top:Issue[];onPart:(p:Part)=>void}){
 const max=Math.max(...data.parts.map((p:Part)=>p.stock_value),1);
 const cats=Object.entries(data.parts.reduce((a:any,p:Part)=>{a[p.category||"Boshqa"]=(a[p.category||"Boshqa"]||0)+p.stock_value;return a},{})).sort((a:any,b:any)=>b[1]-a[1]).slice(0,6);
 return <div className="warehouse-dashboard">
  <div className="dash-grid">
   <section className="pro-panel category-panel"><PanelHead title="Ombor qiymati" subtitle="Kategoriya bo‘yicha taqsimot"/><div className="category-bars">{cats.map(([name,val]:any)=><div className="cat-row" key={name}><div className="cat-label"><span>{name}</span><b>{money(val)}</b></div><div className="bar"><i style={{width:`${Math.max(4,(val/max)*100)}%`}}/></div></div>)}{!cats.length&&<div className="empty">Ma’lumot mavjud emas</div>}</div></section>
   <section className="pro-panel alert-panel"><PanelHead title="Nazorat talab qiladiganlar" subtitle="Minimal qoldiq bo‘yicha"/>{low.slice(0,6).map(p=><button className="alert-row" key={p.id} onClick={()=>onPart(p)}><span className={`status-orb ${p.status.toLowerCase()}`}>{p.status==="CRITICAL"?"!":"!"}</span><span className="alert-main"><b>{p.name}</b><small>{p.code} · min {num(p.min_stock)} {p.unit}</small></span><strong>{num(p.stock)} {p.unit}</strong></button>)}{!low.length&&<div className="success-state">✓ Barcha qoldiqlar me’yorda</div>}</section>
  </div>
  <div className="dash-grid second">
   <section className="pro-panel"><PanelHead title="Eng katta chiqimlar" subtitle="Qiymati bo‘yicha top operatsiyalar"/><div className="mini-list">{top.map(i=><div className="mini-row" key={i.id}><div className="mini-icon"><Wrench size={14}/></div><div className="mini-main"><b>{i.part.name}</b><small>{i.vehicle} · {i.date}</small></div><strong>{money(i.total)}</strong></div>)}{!top.length&&<div className="empty">Chiqimlar mavjud emas</div>}</div></section>
   <section className="pro-panel flow-panel"><PanelHead title="Sklad oqimi" subtitle="So‘nggi operatsiyalar"/><div className="flow-cards"><div><span className="flow-icon in"><ArrowDownToLine size={15}/></span><small>Kirim</small><b>{money(data.summary.receipts_total||0)}</b></div><div><span className="flow-icon out"><ArrowUpFromLine size={15}/></span><small>Chiqim</small><b>{money(data.summary.issues_total||0)}</b></div><div><span className="flow-icon ret"><RotateCcw size={15}/></span><small>Qaytish</small><b>{money(data.summary.returns_total||0)}</b></div></div><div className="warehouse-note"><Truck size={14}/> Chiqimlar avtomobil va servis bilan bog‘langan.</div></section>
  </div>
 </div>
}
function PanelHead({title,subtitle}:{title:string;subtitle:string}){return <div className="pro-panel-head"><div><h2>{title}</h2><p>{subtitle}</p></div><History size={16}/></div>}

function StockTable({rows,onEdit,onCard}:{rows:Part[];onEdit:(x:Part)=>void;onCard:(x:Part)=>void}){
 return <div className="pro-table-card"><div className="table-wrap"><table className="pro-table"><thead><tr><th>Mahsulot</th><th>Kategoriya</th><th>Birlik</th><th>Qoldiq</th><th>Min.</th><th>Weighted avg.</th><th>Qiymat</th><th>Holat</th><th>Amallar</th></tr></thead><tbody>
 {rows.length?rows.map(p=><tr key={p.id}><td><div className="product-cell"><span className="product-avatar"><Package size={15}/></span><span><b>{p.name}</b><small>{p.code}{p.model?` · ${p.model}`:""}</small></span></div></td><td>{p.category||"—"}</td><td>{p.unit}</td><td><b>{num(p.stock)}</b></td><td>{num(p.min_stock)}</td><td>{money(p.unit_price)}</td><td><b>{money(p.stock_value)}</b></td><td><Status status={p.status}/></td><td><div className="row-actions"><button title="Kartochka" onClick={()=>onCard(p)}><Eye size={14}/></button><button title="Tahrirlash" onClick={()=>onEdit(p)}><Pencil size={14}/></button></div></td></tr>):<tr><td colSpan={9}><div className="empty">Mahsulot topilmadi</div></td></tr>}
 </tbody></table></div></div>
}
function Status({status}:{status:Part["status"]}){return <span className={`status-pill ${status.toLowerCase()}`}><i/>{status==="OK"?"Yetarli":status==="LOW"?"Kam qoldi":"Kritik"}</span>}

function ReceiptTable({rows,onEdit}:{rows:Receipt[];onEdit:(x:Receipt)=>void}){return <DataTable headers={["Sana","Mahsulot","Miqdor","Birlik narxi","Jami","Yetkazib beruvchi","Hujjat",""]}>{rows.map(r=><tr key={r.id}><td>{r.date}</td><td><b>{r.part.name}</b><small>{r.part.code}</small></td><td>{num(r.quantity)} {r.part.unit}</td><td>{money(r.unit_price)}</td><td><b>{money(r.total)}</b></td><td>{r.supplier||"—"}</td><td>{r.document_no||"—"}</td><td><button className="table-action" onClick={()=>onEdit(r)}><Pencil size={13}/></button></td></tr>)}</DataTable>}
function IssueTable({rows,onEdit}:{rows:Issue[];onEdit:(x:Issue)=>void}){return <DataTable headers={["Sana","Mahsulot","Avtomobil","Haydovchi","Probeg","Miqdor","Jami","Servis",""]}>{rows.map(i=><tr key={i.id}><td>{i.date}</td><td><b>{i.part.name}</b><small>{i.part.code}</small></td><td><span className="vehicle-chip"><Truck size={12}/>{i.vehicle}</span></td><td>{i.driver||"—"}</td><td>{num(i.odometer)} km</td><td>{num(i.quantity)} {i.part.unit}</td><td><b>{money(i.total)}</b></td><td>{i.maintenance||i.service_type||"—"}</td><td><button className="table-action" onClick={()=>onEdit(i)}><Pencil size={13}/></button></td></tr>)}</DataTable>}
function ReturnTable({rows}:{rows:ReturnRow[]}){return <DataTable headers={["Sana","Mahsulot","Avtomobil","Miqdor","Qiymat","Hujjat","Sabab"]}>{rows.map(r=><tr key={r.id}><td>{r.date}</td><td><b>{r.part.name}</b><small>{r.part.code}</small></td><td>{r.vehicle}</td><td>{num(r.quantity)} {r.part.unit}</td><td><b>{money(r.total)}</b></td><td>{r.document_no||"—"}</td><td>{r.reason||"—"}</td></tr>)}</DataTable>}
function AdjustmentTable({rows}:{rows:Adjustment[]}){return <DataTable headers={["Sana","Mahsulot","Korreksiya","Turi","Qiymat","Sabab","Hujjat"]}>{rows.map(r=><tr key={r.id}><td>{r.date}</td><td><b>{r.part.name}</b><small>{r.part.code}</small></td><td className={r.quantity>0?"positive":"negative"}>{r.quantity>0?"+":""}{num(r.quantity)} {r.part.unit}</td><td><span className={`badge ${r.type==="SURPLUS"?"ok":"danger"}`}>{r.type==="SURPLUS"?"Ortiqcha":"Kamomad"}</span></td><td>{money(r.total)}</td><td>{r.reason}</td><td>{r.document_no||"—"}</td></tr>)}</DataTable>}
function DataTable({headers,children}:{headers:string[];children:React.ReactNode}){return <div className="pro-table-card"><div className="table-wrap"><table className="pro-table"><thead><tr>{headers.map(h=><th key={h}>{h}</th>)}</tr></thead><tbody>{children}</tbody></table></div></div>}

function Modal({title,subtitle,children,onClose,onSave}:{title:string;subtitle:string;children:React.ReactNode;onClose:()=>void;onSave:()=>void}){
 return <div className="modal-backdrop"><div className="modal warehouse-pro-modal"><div className="modal-head"><div><h2>{title}</h2><p>{subtitle}</p></div><button onClick={onClose}><X size={17}/></button></div>{children}<div className="modal-actions"><button className="btn" onClick={onClose}>Bekor qilish</button><button className="btn primary" onClick={onSave}>Saqlash</button></div></div></div>
}
function Field({label,children,full=false}:{label:string;children:React.ReactNode;full?:boolean}){return <label className={full?"full":""}>{label}{children}</label>}
function PartModal({item,onClose,onSaved}:{item:Part|null;onClose:()=>void;onSaved:()=>void}){
 const [form,setForm]=useState<any>(item?{...item}:{code:"",name:"",category:"",model:"",unit:"dona",min_stock:0,unit_price:0});const [error,setError]=useState("");
 const save=async()=>{try{setError("");item?await api.updateWarehousePart(item.id,form):await api.createWarehousePart(form);onSaved()}catch(e){setError(e instanceof Error?e.message:"Saqlashda xatolik")}};
 return <Modal title={item?"Mahsulotni tahrirlash":"Yangi mahsulot"} subtitle="Katalog, limit va boshlang‘ich tannarx sozlamalari." onClose={onClose} onSave={save}><div className="form-grid"><Field label="Artikul / Kod"><input value={form.code} onChange={e=>setForm({...form,code:e.target.value})}/></Field><Field label="Nomi"><input value={form.name} onChange={e=>setForm({...form,name:e.target.value})}/></Field><Field label="Kategoriya"><input value={form.category} onChange={e=>setForm({...form,category:e.target.value})}/></Field><Field label="Mos model"><input value={form.model} onChange={e=>setForm({...form,model:e.target.value})}/></Field><Field label="Birlik"><input value={form.unit} onChange={e=>setForm({...form,unit:e.target.value})}/></Field><Field label="Minimal qoldiq"><input type="number" min="0" step=".01" value={form.min_stock} onChange={e=>setForm({...form,min_stock:e.target.value})}/></Field><Field label="Boshlang‘ich narx"><input type="number" min="0" step=".01" value={form.unit_price} onChange={e=>setForm({...form,unit_price:e.target.value})}/></Field></div>{error&&<div className="form-error">{error}</div>}</Modal>
}
function ReceiptModal({item,parts,onClose,onSaved}:{item:Receipt|null;parts:Part[];onClose:()=>void;onSaved:()=>void}){
 const [form,setForm]=useState<any>(item?{date:item.date,part_id:item.part_id,quantity:item.quantity,unit_price:item.unit_price,compatible_model:item.compatible_model,supplier:item.supplier,document_no:item.document_no,note:item.note}:{date:today(),part_id:parts[0]?.id||"",quantity:1,unit_price:parts[0]?.unit_price||0,compatible_model:"",supplier:"",document_no:"",note:""});const [error,setError]=useState("");
 const choose=(id:any)=>{const p=parts.find(x=>x.id===Number(id));setForm({...form,part_id:Number(id),unit_price:p?.unit_price||0})};
 const save=async()=>{try{setError("");item?await api.updateWarehouseReceipt(item.id,form):await api.createWarehouseReceipt(form);onSaved()}catch(e){setError(e instanceof Error?e.message:"Saqlashda xatolik")}};
 return <Modal title={item?"Kirimni tahrirlash":"Yangi kirim"} subtitle="Yetkazib beruvchi, hujjat va real xarid narxini kiriting." onClose={onClose} onSave={save}><div className="form-grid"><Field label="Sana"><input type="date" value={form.date} onChange={e=>setForm({...form,date:e.target.value})}/></Field><Field label="Mahsulot"><select value={form.part_id} onChange={e=>choose(e.target.value)}>{parts.map(p=><option key={p.id} value={p.id}>{p.name} · {p.code}</option>)}</select></Field><Field label="Miqdor"><input type="number" min=".01" step=".01" value={form.quantity} onChange={e=>setForm({...form,quantity:e.target.value})}/></Field><Field label="Birlik narxi"><input type="number" min="0" step=".01" value={form.unit_price} onChange={e=>setForm({...form,unit_price:e.target.value})}/></Field><Field label="Yetkazib beruvchi"><input value={form.supplier} onChange={e=>setForm({...form,supplier:e.target.value})}/></Field><Field label="Hujjat raqami"><input value={form.document_no} onChange={e=>setForm({...form,document_no:e.target.value})}/></Field><Field label="Mos model"><input value={form.compatible_model} onChange={e=>setForm({...form,compatible_model:e.target.value})}/></Field><Field label="Izoh"><input value={form.note} onChange={e=>setForm({...form,note:e.target.value})}/></Field></div>{error&&<div className="form-error">{error}</div>}</Modal>
}
function IssueModal({item,parts,meta,onClose,onSaved}:{item:Issue|null;parts:Part[];meta:Meta;onClose:()=>void;onSaved:()=>void}){
 const [form,setForm]=useState<any>(item?{date:item.date,part_id:item.part_id,vehicle_id:item.vehicle_id,driver_id:item.driver_id||"",maintenance_id:item.maintenance_id||"",odometer:item.odometer,quantity:item.quantity,unit_price:item.unit_price,service_type:item.service_type,note:item.note}:{date:today(),part_id:parts[0]?.id||"",vehicle_id:meta.vehicles[0]?.id||"",driver_id:"",maintenance_id:"",odometer:meta.vehicles[0]?.mileage||0,quantity:1,unit_price:parts[0]?.unit_price||0,service_type:"",note:""});const [error,setError]=useState("");
 const choosePart=(id:any)=>{const p=parts.find(x=>x.id===Number(id));setForm({...form,part_id:Number(id),unit_price:p?.unit_price||0})};
 const chooseVehicle=(id:any)=>setForm({...form,vehicle_id:Number(id),odometer:meta.vehicles.find(v=>v.id===Number(id))?.mileage||0,driver_id:"",maintenance_id:""});
 const save=async()=>{try{setError("");item?await api.updateWarehouseIssue(item.id,form):await api.createWarehouseIssue(form);onSaved()}catch(e){setError(e instanceof Error?e.message:"Saqlashda xatolik")}};
 const p=parts.find(x=>x.id===Number(form.part_id));
 return <Modal title={item?"Chiqimni tahrirlash":"Yangi chiqim"} subtitle="Qoldiq tekshiriladi va Finance’da Sklad xarajati avtomatik yaratiladi." onClose={onClose} onSave={save}><div className="form-grid"><Field label="Sana"><input type="date" value={form.date} onChange={e=>setForm({...form,date:e.target.value})}/></Field><Field label="Mahsulot"><select value={form.part_id} onChange={e=>choosePart(e.target.value)}>{parts.map(p=><option key={p.id} value={p.id}>{p.name} · {p.code}</option>)}</select></Field><Field label="Avtomobil"><select value={form.vehicle_id} onChange={e=>chooseVehicle(e.target.value)}>{meta.vehicles.map(v=><option key={v.id} value={v.id}>{v.number} · {v.model}</option>)}</select></Field><Field label="Haydovchi"><select value={form.driver_id} onChange={e=>setForm({...form,driver_id:e.target.value})}><option value="">Tanlanmagan</option>{meta.drivers.filter(d=>!d.vehicle_id||d.vehicle_id===Number(form.vehicle_id)).map(d=><option key={d.id} value={d.id}>{d.name}</option>)}</select></Field><Field label="Servis rejasi"><select value={form.maintenance_id} onChange={e=>setForm({...form,maintenance_id:e.target.value})}><option value="">Tanlanmagan</option>{meta.maintenance.filter(m=>m.vehicle_id===Number(form.vehicle_id)).map(m=><option key={m.id} value={m.id}>{m.name}</option>)}</select></Field><Field label="Probeg"><input type="number" min="0" step=".1" value={form.odometer} onChange={e=>setForm({...form,odometer:e.target.value})}/></Field><Field label="Miqdor"><input type="number" min=".01" step=".01" value={form.quantity} onChange={e=>setForm({...form,quantity:e.target.value})}/></Field><Field label="Birlik narxi"><input type="number" min="0" step=".01" value={form.unit_price} onChange={e=>setForm({...form,unit_price:e.target.value})}/></Field><Field label="Servis turi"><input value={form.service_type} onChange={e=>setForm({...form,service_type:e.target.value})}/></Field><Field label="Izoh"><input value={form.note} onChange={e=>setForm({...form,note:e.target.value})}/></Field></div><div className="stock-warning"><AlertTriangle size={15}/> Mavjud qoldiq: <b>{num(p?.stock||0)} {p?.unit||""}</b></div>{error&&<div className="form-error">{error}</div>}</Modal>
}
function ReturnModal({issues,onClose,onSaved}:{issues:Issue[];onClose:()=>void;onSaved:()=>void}){
 const [form,setForm]=useState<any>({date:today(),issue_id:issues[0]?.id||"",quantity:1,document_no:"",reason:"",note:""});const [error,setError]=useState("");
 const issue=issues.find(i=>i.id===Number(form.issue_id));
 const used=issue?0:0;
 const save=async()=>{try{setError("");await api.createWarehouseReturn(form);onSaved()}catch(e){setError(e instanceof Error?e.message:"Saqlashda xatolik")}};
 return <Modal title="Skladga qaytarish" subtitle="Oldingi chiqimdan qaytarilgan ehtiyot qismni omborga qaytaring." onClose={onClose} onSave={save}><div className="form-grid"><Field label="Sana"><input type="date" value={form.date} onChange={e=>setForm({...form,date:e.target.value})}/></Field><Field label="Chiqim"><select value={form.issue_id} onChange={e=>setForm({...form,issue_id:Number(e.target.value)})}>{issues.map(i=><option key={i.id} value={i.id}>{i.date} · {i.vehicle} · {i.part.name} · {num(i.quantity)} {i.part.unit}</option>)}</select></Field><Field label="Miqdor"><input type="number" min=".01" step=".01" value={form.quantity} onChange={e=>setForm({...form,quantity:e.target.value})}/></Field><Field label="Hujjat raqami"><input value={form.document_no} onChange={e=>setForm({...form,document_no:e.target.value})}/></Field><Field label="Sabab"><input value={form.reason} onChange={e=>setForm({...form,reason:e.target.value})}/></Field><Field label="Izoh"><input value={form.note} onChange={e=>setForm({...form,note:e.target.value})}/></Field></div>{issue&&<div className="return-preview"><b>{issue.part.name}</b><span>{issue.vehicle}</span><strong>{money(issue.unit_price)}/birlik</strong></div>}{error&&<div className="form-error">{error}</div>}</Modal>
}
function AdjustmentModal({parts,onClose,onSaved}:{parts:Part[];onClose:()=>void;onSaved:()=>void}){
 const [form,setForm]=useState<any>({date:today(),part_id:parts[0]?.id||"",quantity:1,unit_price:parts[0]?.unit_price||0,reason:"Inventarizatsiya",document_no:"",note:""});const [error,setError]=useState("");
 const choose=(id:any)=>{const p=parts.find(x=>x.id===Number(id));setForm({...form,part_id:Number(id),unit_price:p?.unit_price||0})};
 const save=async()=>{try{setError("");await api.createWarehouseAdjustment(form);onSaved()}catch(e){setError(e instanceof Error?e.message:"Saqlashda xatolik")}};
 return <Modal title="Inventarizatsiya / Korreksiya" subtitle="+ ortiqcha, − kamomad. Manfiy qoldiqka ruxsat berilmaydi." onClose={onClose} onSave={save}><div className="form-grid"><Field label="Sana"><input type="date" value={form.date} onChange={e=>setForm({...form,date:e.target.value})}/></Field><Field label="Mahsulot"><select value={form.part_id} onChange={e=>choose(e.target.value)}>{parts.map(p=><option key={p.id} value={p.id}>{p.name} · {p.code}</option>)}</select></Field><Field label="Korreksiya miqdori"><input type="number" step=".01" value={form.quantity} onChange={e=>setForm({...form,quantity:e.target.value})}/></Field><Field label="Birlik narxi"><input type="number" min="0" step=".01" value={form.unit_price} onChange={e=>setForm({...form,unit_price:e.target.value})}/></Field><Field label="Sabab"><input value={form.reason} onChange={e=>setForm({...form,reason:e.target.value})}/></Field><Field label="Hujjat"><input value={form.document_no} onChange={e=>setForm({...form,document_no:e.target.value})}/></Field><Field label="Izoh" full><input value={form.note} onChange={e=>setForm({...form,note:e.target.value})}/></Field></div>{error&&<div className="form-error">{error}</div>}</Modal>
}
function CardModal({part,onClose}:{part:Part;onClose:()=>void}){
 const [data,setData]=useState<any>(null);useEffect(()=>{api.warehouseCard(part.id).then(setData).catch(()=>setData({rows:[]}))},[part.id]);
 return <div className="modal-backdrop"><div className="modal card-modal"><div className="modal-head"><div><h2>{part.name}</h2><p>{part.code} · Ombor kartochkasi</p></div><button onClick={onClose}><X size={17}/></button></div><div className="card-summary"><div><span>Qoldiq</span><b>{num(data?.part?.stock??part.stock)} {part.unit}</b></div><div><span>Tannarx</span><b>{money(data?.part?.unit_price??part.unit_price)}</b></div><div><span>Qiymat</span><b>{money(data?.part?.stock_value??part.stock_value)}</b></div></div><div className="movement-list">{(data?.rows||[]).map((r:any,i:number)=><div className="movement-row" key={i}><span className={`movement-dot ${r.type.toLowerCase()}`}/><div><b>{r.type}</b><small>{r.date} · {r.counterparty||"—"}</small></div><strong className={r.quantity>0?"positive":"negative"}>{r.quantity>0?"+":""}{num(r.quantity)} {part.unit}<small>{money(r.total)}</small></strong></div>)}</div></div></div>
}
