import React, { useEffect, useState } from "react";
import { BookOpen, MapPin, FileCheck2, ShieldCheck, LayoutDashboard, Menu, X, Upload, Loader2, ArrowRight, CheckCircle2, AlertCircle, ExternalLink } from "lucide-react";

const API = import.meta.env.VITE_API_URL || "http://127.0.0.1:8000";
const modules = [
  { id:"home", name:"Overview", icon:LayoutDashboard, desc:"Your civic intelligence hub" },
  { id:"policy", name:"PolicyLens", icon:BookOpen, desc:"Understand policies and schemes" },
  { id:"civic", name:"CivicWatch", icon:MapPin, desc:"Report local civic issues" },
  { id:"seva", name:"SevaBot", icon:FileCheck2, desc:"Navigate public services" },
  { id:"truth", name:"TruthScan", icon:ShieldCheck, desc:"Evaluate claims with evidence" },
];
async function request(path, options={}) {
  const res = await fetch(`${API}${path}`, options);
  const data = await res.json().catch(()=>({detail:"Unexpected server response"}));
  if (!res.ok) throw new Error(data.detail || "Request failed");
  return data;
}
function Result({data}) {
  if (!data) return null;
  return <div className="result"><h3>Result</h3>{Object.entries(data).map(([k,v])=><div className="result-row" key={k}><b>{k.replaceAll("_"," ")}</b><div>{Array.isArray(v) ? <ul>{v.map((x,i)=><li key={i}>{typeof x==="object"?JSON.stringify(x):String(x)}</li>)}</ul> : typeof v==="object" && v!==null ? JSON.stringify(v) : String(v)}</div></div>)}</div>;
}
function App() {
  const [active,setActive]=useState("home"), [mobile,setMobile]=useState(false);
  const [stats,setStats]=useState(null), [error,setError]=useState("");
  async function refresh(){ try{setStats(await request("/api/dashboard/stats"));}catch(e){setError(e.message);} }
  useEffect(()=>{refresh()},[]);
  const current=modules.find(m=>m.id===active);
  return <div className="app-shell">
    <aside className={`sidebar ${mobile?"open":""}`}>
      <div className="brand"><div className="brand-mark">J</div><div><b>JANSETU AI</b><small>Civic Intelligence</small></div><button className="mobile-close" onClick={()=>setMobile(false)}><X/></button></div>
      <div className="nav-label">WORKSPACE</div>
      {modules.map(m=><button key={m.id} className={`nav-item ${active===m.id?"active":""}`} onClick={()=>{setActive(m.id);setMobile(false)}}><m.icon size={18}/><span>{m.name}</span>{active===m.id&&<span className="nav-dot"/>}</button>)}
      <div className="sidebar-bottom"><div className="status-dot"/> Prototype environment <small>Not an official government portal</small></div>
    </aside>
    {mobile&&<div className="scrim" onClick={()=>setMobile(false)}/>}
    <main className="main">
      <header className="topbar"><button className="mobile-menu" onClick={()=>setMobile(true)}><Menu/></button><div><span className="eyebrow">CITIZEN SERVICES / {current.name.toUpperCase()}</span><h2>{current.name}</h2></div><div className="top-right"><span className="online"><i/> AI services</span><div className="avatar">C</div></div></header>
      {error&&<div className="alert error"><AlertCircle size={17}/>{error} — Is the FastAPI server running?</div>}
      <div className="content">
        {active==="home"&&<Dashboard stats={stats} navigate={setActive} refresh={refresh}/>}
        {active==="policy"&&<Policy/>}
        {active==="civic"&&<Civic refresh={refresh}/>}
        {active==="seva"&&<Seva/>}
        {active==="truth"&&<Truth/>}
      </div>
      <footer>JANSETU AI · Hackathon prototype · Verify important information with official authorities.</footer>
    </main>
  </div>
}
function PageIntro({kicker,title,desc}){return <div className="page-intro"><div className="eyebrow">{kicker}</div><h1>{title}</h1><p>{desc}</p></div>}
function Dashboard({stats,navigate,refresh}) {
  return <><section className="hero"><div><span className="hero-tag">ONE PLATFORM · FOUR INTELLIGENT MODULES</span><h1>Make civic services<br/><em>work for everyone.</em></h1><p>Understand public policies, report local issues, navigate services and examine claims with evidence.</p><button className="btn light" onClick={()=>navigate("policy")}>Explore services <ArrowRight size={16}/></button></div><div className="hero-orb"><div className="orb-inner">J<span>AI</span></div><div className="orbit orbit-one"/><div className="orbit orbit-two"/></div></section>
  <div className="section-head"><div><div className="eyebrow">YOUR WORKSPACE</div><h2>Four ways we can help</h2></div></div>
  <div className="module-grid">{modules.slice(1).map((m,i)=><button className="module-card" key={m.id} onClick={()=>navigate(m.id)}><div className={`module-icon tone-${i}`}><m.icon size={22}/></div><h3>{m.name}</h3><p>{m.desc}</p><span className="card-link">Open module <ArrowRight size={15}/></span></button>)}</div>
  <div className="section-head stats-head"><div><div className="eyebrow">LIVE FROM YOUR LOCAL DEMO DATABASE</div><h2>Activity overview</h2></div><button className="btn outline" onClick={refresh}>Refresh</button></div>
  <div className="stats-grid"><Stat label="Civic complaints" value={stats?.complaints??"—"} icon={MapPin}/><Stat label="Service assessments" value={stats?.applications??"—"} icon={FileCheck2}/><Stat label="Verification reports" value={stats?.verifications??"—"} icon={ShieldCheck}/></div>
  <div className="notice"><ShieldCheck size={19}/><div><b>Evidence-first civic AI</b><p>AI outputs are decision-support suggestions. Check official sources before acting; this prototype does not submit applications or contact authorities.</p></div></div>
  </>;
}
function Stat({label,value,icon:Icon}){return <div className="stat-card"><div className="stat-icon"><Icon size={18}/></div><strong>{value}</strong><span>{label}</span></div>}
function Panel({children}){return <div className="panel">{children}</div>}
function BusyButton({busy,children}){return <button className="btn primary" disabled={busy}>{busy?<><Loader2 className="spin" size={16}/> Working…</>:children}</button>}
function Policy(){
  const [file,setFile]=useState(null),[language,setLanguage]=useState("English"),[data,setData]=useState(null),[busy,setBusy]=useState(false),[error,setError]=useState("");
  async function submit(e){e.preventDefault();if(!file)return;setBusy(true);setError("");setData(null);try{const fd=new FormData();fd.append("file",file);fd.append("language",language);setData(await request("/api/policy/analyze",{method:"POST",body:fd}));}catch(x){setError(x.message)}finally{setBusy(false)}}
  return <><PageIntro kicker="MODULE 01 · POLICY INTELLIGENCE" title="Understand what the rules mean." desc="Upload a government notification or scheme PDF. PolicyLens turns complex language into a structured, plain-language guide."/><Panel><form onSubmit={submit}><label>Government notification (PDF)</label><label className="upload-box"><Upload size={25}/><b>{file?file.name:"Choose a PDF file"}</b><span>Text-based PDF · Maximum 12 MB</span><input type="file" accept="application/pdf" onChange={e=>setFile(e.target.files[0])}/></label><label>Explanation language</label><select value={language} onChange={e=>setLanguage(e.target.value)}><option>English</option><option>Hindi</option><option>Bengali</option><option>Odia</option></select><BusyButton busy={busy}><Upload size={16}/> Analyze document</BusyButton></form>{error&&<div className="alert error">{error}</div>}</Panel>{data&&<Result data={data}/>}</>
}
function Civic({refresh}){
  const [file,setFile]=useState(null),[desc,setDesc]=useState(""),[location,setLocation]=useState(""),[data,setData]=useState(null),[saved,setSaved]=useState(null),[busy,setBusy]=useState(false),[error,setError]=useState("");
  async function classify(e){e.preventDefault();if(!file)return;setBusy(true);setError("");setSaved(null);try{const fd=new FormData();fd.append("file",file);fd.append("description",desc);fd.append("location",location);setData(await request("/api/civic/classify",{method:"POST",body:fd}));}catch(x){setError(x.message)}finally{setBusy(false)}}
  async function save(){try{const d=await request("/api/civic/submit",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({category:data.category,severity:data.severity,description:data.description,department:data.suggested_department,location})});setSaved(d);refresh();}catch(x){setError(x.message)}}
  return <><PageIntro kicker="MODULE 02 · CIVIC ACCOUNTABILITY" title="See a problem. Help get it noticed." desc="Submit a photo and description of a local issue. AI suggests a category and urgency for human review."/><Panel><form onSubmit={classify}><label>Issue photograph</label><label className="upload-box"><MapPin size={25}/><b>{file?file.name:"Upload an issue photo"}</b><span>JPG, PNG or WEBP · Maximum 8 MB</span><input type="file" accept="image/png,image/jpeg,image/webp" onChange={e=>setFile(e.target.files[0])}/></label><label>What happened?</label><textarea value={desc} onChange={e=>setDesc(e.target.value)} placeholder="e.g. Large pothole near the bus stop..." rows="3"/><label>Area / landmark (optional)</label><input value={location} onChange={e=>setLocation(e.target.value)} placeholder="e.g. Near City Park"/><BusyButton busy={busy}>Analyze issue <ArrowRight size={16}/></BusyButton></form>{error&&<div className="alert error">{error}</div>}</Panel>{data&&<><Result data={data}/><button className="btn primary" onClick={save}><CheckCircle2 size={16}/> Submit complaint to demo tracker</button></>}{saved&&<div className="alert success">Complaint saved. Tracking ID: <b>{saved.id}</b></div>}</>
}
function Seva(){
  const [service,setService]=useState("Student scholarship"),[rules,setRules]=useState(""),[details,setDetails]=useState(""),[language,setLanguage]=useState("English"),[data,setData]=useState(null),[busy,setBusy]=useState(false),[error,setError]=useState("");
  async function submit(e){e.preventDefault();setBusy(true);setError("");setData(null);try{setData(await request("/api/seva/check-eligibility",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({service_name:service,official_rules:rules,applicant_details:details,language})}));}catch(x){setError(x.message)}finally{setBusy(false)}}
  return <><PageIntro kicker="MODULE 03 · PUBLIC SERVICE NAVIGATION" title="Make the next step clearer." desc="Compare applicant information with official rules you provide. SevaBot produces a preliminary checklist and application guidance."/><Panel><form onSubmit={submit}><label>Service or scheme name</label><input value={service} onChange={e=>setService(e.target.value)} required/><label>Official eligibility rules</label><textarea rows="5" value={rules} onChange={e=>setRules(e.target.value)} placeholder="Paste eligibility criteria from an official notification or website. Include the source name..." required minLength="20"/><label>Applicant details (avoid sensitive IDs)</label><textarea rows="4" value={details} onChange={e=>setDetails(e.target.value)} placeholder="Example: I am an undergraduate student. Family income is within the stated limit..." required/><label>Response language</label><select value={language} onChange={e=>setLanguage(e.target.value)}><option>English</option><option>Hindi</option><option>Bengali</option><option>Odia</option></select><BusyButton busy={busy}>Check against supplied rules <ArrowRight size={16}/></BusyButton></form>{error&&<div className="alert error">{error}</div>}</Panel>{data&&<Result data={data}/>}</>
}
function Truth(){
  const [claim,setClaim]=useState(""),[evidence,setEvidence]=useState(""),[urls,setUrls]=useState(""),[data,setData]=useState(null),[busy,setBusy]=useState(false),[error,setError]=useState("");
  async function submit(e){e.preventDefault();setBusy(true);setError("");setData(null);try{setData(await request("/api/truth/verify",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({claim,evidence,source_urls:urls.split("\n").map(x=>x.trim()).filter(Boolean)})}));}catch(x){setError(x.message)}finally{setBusy(false)}}
  return <><PageIntro kicker="MODULE 04 · INFORMATION INTEGRITY" title="Slow down. Check the evidence." desc="Submit a claim and paste source excerpts. TruthScan compares the claim with the evidence you provide; it does not independently crawl the web in this MVP."/><Panel><form onSubmit={submit}><label>Claim to examine</label><textarea rows="3" value={claim} onChange={e=>setClaim(e.target.value)} placeholder="Paste the exact statement you want to check..." required minLength="8"/><label>Evidence excerpts (recommended)</label><textarea rows="5" value={evidence} onChange={e=>setEvidence(e.target.value)} placeholder="Paste relevant text from official or trusted sources. Include dates and context..."/><label>Source URLs (one per line; not automatically fetched)</label><textarea rows="2" value={urls} onChange={e=>setUrls(e.target.value)} placeholder="https://official-source.gov.in/..."/><BusyButton busy={busy}>Analyze claim <ShieldCheck size={16}/></BusyButton></form>{error&&<div className="alert error">{error}</div>}</Panel>{data&&<><Result data={data}/>{data.verdict==="Unverified"&&<div className="notice"><AlertCircle size={18}/><div><b>Not enough evidence</b><p>Unverified does not mean false. Find an authoritative source before sharing or acting on the claim.</p></div></div>}</>}</>
}
export default App;
