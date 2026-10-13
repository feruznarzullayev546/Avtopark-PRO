import {useEffect,useMemo,useRef,useState} from 'react';
import {MessageCircle,Search,Send,UserRound,ShieldCheck,RefreshCw} from 'lucide-react';
import {api,chatWebSocket} from '../services/api';

type Contact={user:{id:number;name:string;username:string;role:string;avatar_url?:string|null};conversation_id:number|null;last_message?:string|null;last_at?:string|null;unread:number};
type Message={id:number;sender_id:number;body:string;created_at:string;read_at?:string|null};

const roleLabel=(r:string)=>({SUPER_ADMIN:'Super Admin',DIRECTOR:'Direktor',MANAGER:'Manager',DRIVER:'Haydovchi'} as Record<string,string>)[r]||r;
const time=(v?:string|null)=>v?new Date(v).toLocaleTimeString('uz-UZ',{hour:'2-digit',minute:'2-digit'}):'';

export function Chat(){
 const [contacts,setContacts]=useState<Contact[]>([]); const [selected,setSelected]=useState<Contact|null>(null); const [messages,setMessages]=useState<Message[]>([]); const [draft,setDraft]=useState(''); const [loading,setLoading]=useState(true); const [sending,setSending]=useState(false); const [search,setSearch]=useState(''); const [wsState,setWsState]=useState<'connecting'|'open'|'closed'>('closed'); const endRef=useRef<HTMLDivElement|null>(null); const wsRef=useRef<WebSocket|null>(null);
 const loadContacts=async()=>{try{const r=await api.chatContacts();setContacts(r.contacts||[]); if(!selected && r.contacts?.length)setSelected(r.contacts[0]);}finally{setLoading(false)}};
 const loadConversation=async(c:Contact)=>{setSelected(c); const r=await api.chatConversation(c.user.id); setMessages(r.messages||[]); setContacts(prev=>prev.map(x=>x.user.id===c.user.id?{...x,unread:0,conversation_id:r.conversation?.id||x.conversation_id}:x));};
 useEffect(()=>{loadContacts().catch(()=>setLoading(false));},[]);
 useEffect(()=>{if(selected)loadConversation(selected).catch(()=>{});},[selected?.user.id]);
 useEffect(()=>{
   wsRef.current?.close();
   if(!selected) return;
   setWsState('connecting');
   const ws=chatWebSocket(selected.user.id); wsRef.current=ws;
   ws.onopen=()=>setWsState('open');
   ws.onclose=()=>setWsState('closed');
   ws.onerror=()=>setWsState('closed');
   ws.onmessage=(ev)=>{try{const event=JSON.parse(ev.data); if(event.type==='message'){setMessages(prev=>prev.some(m=>m.id===event.message.id)?prev:[...prev,event.message]); setContacts(prev=>prev.map(c=>c.user.id===selected.user.id?{...c,last_message:event.message.body,last_at:event.message.created_at,conversation_id:event.conversation_id,unread:0}:c));}}catch{}};
   return()=>{ws.close(); if(wsRef.current===ws)wsRef.current=null};
 },[selected?.user.id]);
 useEffect(()=>{endRef.current?.scrollIntoView({behavior:'smooth'})},[messages.length]);
 const visible=useMemo(()=>contacts.filter(c=>`${c.user.name} ${c.user.role} ${c.user.username}`.toLowerCase().includes(search.toLowerCase())),[contacts,search]);
 const send=async()=>{const body=draft.trim();if(!body||!selected||sending)return;setSending(true);try{if(wsRef.current?.readyState===WebSocket.OPEN){wsRef.current.send(JSON.stringify({event:'message',body}));setDraft('');}else{const r=await api.sendChatMessage(selected.user.id,body);setMessages(m=>m.some(x=>x.id===r.message.id)?m:[...m,r.message]);setDraft('');loadContacts().catch(()=>{});}}finally{setSending(false)}};
 return <div className="page chat-page">
   
   <div className="chat-layout">
    <section className="panel chat-contacts">
      <div className="chat-panel-head"><div><strong>Suhbatlar</strong><span>{contacts.length} ta kontakt</span></div><MessageCircle size={18}/></div>
      <div className="chat-search"><Search size={15}/><input placeholder="Kontakt qidirish..." value={search} onChange={e=>setSearch(e.target.value)}/></div>
      <div className="chat-contact-list">{loading?<div className="chat-empty">Yuklanmoqda...</div>:visible.length?visible.map(c=><button key={c.user.id} className={`chat-contact ${selected?.user.id===c.user.id?'active':''}`} onClick={()=>loadConversation(c)}><div className="chat-avatar">{c.user.avatar_url?<img src={c.user.avatar_url} alt=""/>:<UserRound size={17}/>}</div><div className="chat-contact-main"><strong>{c.user.name}</strong><span>{roleLabel(c.user.role)}</span><small>{c.last_message||'Yangi suhbatni boshlang'}</small></div><div className="chat-contact-meta">{c.last_at&&<time>{time(c.last_at)}</time>}{c.unread>0&&<b>{c.unread}</b>}</div></button>):<div className="chat-empty"><MessageCircle size={28}/><strong>Kontaktlar mavjud emas</strong><span>Sizning rolingizga mos shaxsiy chatlar shu yerda chiqadi.</span></div>}</div>
    </section>
    <section className="panel chat-window">
      {selected?<><div className="chat-window-head"><div className="chat-avatar large">{selected.user.avatar_url?<img src={selected.user.avatar_url} alt=""/>:<UserRound size={20}/>}</div><div><strong>{selected.user.name}</strong><span>{roleLabel(selected.user.role)} · Shaxsiy chat</span></div><div className={`chat-secure ${wsState==='open'?'ws-online':'ws-offline'}`}><ShieldCheck size={15}/> Private · {wsState==='open'?'Real-time':'Ulanmoqda...'}</div></div>
      <div className="chat-messages">{messages.length?messages.map(m=><div key={m.id} className={`chat-message ${m.sender_id===selected.user.id?'incoming':'outgoing'}`}><div>{m.body}</div><time>{time(m.created_at)}</time></div>):<div className="chat-empty conversation-empty"><MessageCircle size={34}/><strong>Shaxsiy suhbat</strong><span>Bu kontakt bilan birinchi xabarni yuboring.</span></div>}<div ref={endRef}/></div>
      <div className="chat-compose"><textarea value={draft} onChange={e=>setDraft(e.target.value)} onKeyDown={e=>{if(e.key==='Enter'&&!e.shiftKey){e.preventDefault();send()}}} placeholder="Xabar yozing..." maxLength={5000}/><button className="btn primary" disabled={!draft.trim()||sending} onClick={send}><Send size={15}/> Yuborish</button></div></>:<div className="chat-empty conversation-empty"><MessageCircle size={42}/><strong>Chatni tanlang</strong><span>Chap tomondan ruxsat berilgan kontaktlardan birini tanlang.</span></div>}
    </section>
   </div>
 </div>
}
