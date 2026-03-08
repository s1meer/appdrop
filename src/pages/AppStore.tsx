import { useState } from "react"
import { RegistryApp, api } from "../lib/api"
import { useRegistry } from "../hooks/useRegistry"

const STACK_ICON: Record<string,string> = { python:"🐍", node:"💚", docker:"🐳", conda:"🅒", unknown:"?" }
const TAG_COLORS: Record<string,string> = { ai:"#7C4DFF", "stable-diffusion":"#FF6B6B",
  llm:"#4F8EF7", chat:"#2ECC71", nocode:"#F39C12", transcription:"#00BCD4",
  automation:"#FF9800", api:"#9C27B0", "image-generation":"#E91E63" }

interface CardProps { app: RegistryApp; theme:"dark"|"light"; onInstall:(a:RegistryApp)=>void }

function AppCard({ app, theme, onInstall }: CardProps) {
  const bg = theme==="dark" ? "#141720" : "#FFFFFF"
  const border = theme==="dark" ? "#1E2235" : "#D8DCF0"
  const text = theme==="dark" ? "#E8EAF0" : "#1A1D2E"
  const sub = theme==="dark" ? "#5A6278" : "#8A8FA8"

  return (
    <div style={{background:bg,border:`1px solid ${app.installed?"#4F8EF7":border}`,
      borderRadius:12,padding:20,cursor:"pointer",transition:"all 0.15s"}}
      onMouseEnter={e=>{e.currentTarget.style.borderColor="#4F8EF7";e.currentTarget.style.transform="translateY(-2px)"}}
      onMouseLeave={e=>{e.currentTarget.style.borderColor=app.installed?"#4F8EF7":border;e.currentTarget.style.transform=""}}>
      <div style={{display:"flex",justifyContent:"space-between",alignItems:"flex-start",marginBottom:10}}>
        <div style={{display:"flex",alignItems:"center",gap:10}}>
          <span style={{fontSize:28}}>{STACK_ICON[app.stack]||"?"}</span>
          <div>
            <div style={{color:text,fontWeight:700,fontSize:14}}>{app.name}</div>
            <div style={{color:"#F39C12",fontSize:11}}>
              ⭐ {(app.stars_approx/1000).toFixed(1)}k
              {app.verified && <span style={{color:"#4F8EF7",marginLeft:6}}>✓ verified</span>}
            </div>
          </div>
        </div>
        <button onClick={()=>onInstall(app)} disabled={app.installed}
          style={{background:app.installed?"none":"#4F8EF7",
            border:app.installed?`1px solid ${border}`:"none",
            borderRadius:7,padding:"6px 12px",color:app.installed?sub:"#fff",
            fontSize:12,fontWeight:600,cursor:app.installed?"default":"pointer",
            flexShrink:0}}>
          {app.installed ? "Installed ✓" : "Install"}
        </button>
      </div>
      <p style={{color:sub,fontSize:12,margin:"0 0 10px",lineHeight:1.5}}>
        {app.description.slice(0,90)}{app.description.length>90?"...":""}
      </p>
      <div style={{display:"flex",flexWrap:"wrap",gap:5}}>
        {app.tags.slice(0,4).map(t=>(
          <span key={t} style={{background:TAG_COLORS[t]||"rgba(79,142,247,0.15)",
            color:TAG_COLORS[t]?"#fff":"#4F8EF7",borderRadius:4,
            padding:"2px 7px",fontSize:10,fontWeight:600}}>{t}</span>
        ))}
      </div>
    </div>
  )
}

interface Props { theme:"dark"|"light"; onInstallUrl:(url:string,name:string)=>void }

export default function AppStore({ theme, onInstallUrl }: Props) {
  const [search, setSearch] = useState("")
  const [stackFilter, setStackFilter] = useState("")
  const [tagFilter, setTagFilter] = useState("")
  const [showSubmit, setShowSubmit] = useState(false)
  const [submitForm, setSubmitForm] = useState({github_url:"",name:"",description:"",stack:"python"})
  const [submitMsg, setSubmitMsg] = useState("")

  const { apps, loading } = useRegistry({
    q: search||undefined,
    stack: stackFilter||undefined,
    tag: tagFilter||undefined,
  })

  const text = theme==="dark" ? "#E8EAF0" : "#1A1D2E"
  const sub  = theme==="dark" ? "#5A6278" : "#8A8FA8"
  const bg2  = theme==="dark" ? "#141720" : "#FFFFFF"
  const border = theme==="dark" ? "#1E2235" : "#D8DCF0"
  const input  = theme==="dark" ? "#0D0F15" : "#F4F6FF"

  async function submitApp() {
    try {
      await api.submitApp(submitForm)
      setSubmitMsg("✅ Submitted! Under review."); setSubmitForm({github_url:"",name:"",description:"",stack:"python"})
    } catch { setSubmitMsg("❌ Invalid URL or already exists") }
  }

  return (
    <div style={{flex:1,overflow:"auto",padding:32}}>
      <div style={{display:"flex",justifyContent:"space-between",alignItems:"center",marginBottom:24}}>
        <div>
          <h1 style={{color:text,fontSize:22,fontWeight:800,margin:0}}>App Store</h1>
          <p style={{color:sub,fontSize:13,margin:"4px 0 0"}}>{apps.length} apps available</p>
        </div>
        <button onClick={()=>setShowSubmit(!showSubmit)}
          style={{background:"none",border:`1px solid ${border}`,borderRadius:8,
            padding:"9px 16px",color:sub,fontSize:13,cursor:"pointer"}}>
          + Submit App
        </button>
      </div>

      {/* Filters */}
      <div style={{display:"flex",gap:10,marginBottom:24,flexWrap:"wrap"}}>
        <input value={search} onChange={e=>setSearch(e.target.value)}
          placeholder="Search apps..."
          style={{flex:1,minWidth:200,background:input,border:`1px solid ${border}`,
            borderRadius:8,padding:"9px 12px",color:text,fontSize:13,outline:"none"}}/>
        {["","python","node","docker"].map(s=>(
          <button key={s} onClick={()=>setStackFilter(s)}
            style={{background:stackFilter===s?"#4F8EF7":"none",
              border:`1px solid ${stackFilter===s?"#4F8EF7":border}`,
              borderRadius:7,padding:"8px 14px",
              color:stackFilter===s?"#fff":sub,fontSize:12,cursor:"pointer"}}>
            {s||"All"} {s && STACK_ICON[s]}
          </button>
        ))}
        {["","ai","llm","chat","image-generation","nocode"].map(t=>(
          <button key={t} onClick={()=>setTagFilter(t)}
            style={{background:tagFilter===t?(TAG_COLORS[t]||"#4F8EF7"):"none",
              border:`1px solid ${tagFilter===t?(TAG_COLORS[t]||"#4F8EF7"):border}`,
              borderRadius:7,padding:"8px 14px",
              color:tagFilter===t?"#fff":sub,fontSize:12,cursor:"pointer"}}>
            {t||"All Tags"}
          </button>
        ))}
      </div>

      {/* Submit form */}
      {showSubmit && (
        <div style={{background:bg2,border:`1px solid ${border}`,borderRadius:12,
          padding:20,marginBottom:24}}>
          <h3 style={{color:text,margin:"0 0 14px",fontSize:15}}>Submit a Community App</h3>
          <div style={{display:"grid",gridTemplateColumns:"1fr 1fr",gap:10,marginBottom:10}}>
            {[["github_url","GitHub URL"],["name","App Name"],["description","Description (optional)"]].map(([k,p])=>(
              <input key={k} placeholder={p} value={(submitForm as any)[k]}
                onChange={e=>setSubmitForm(f=>({...f,[k]:e.target.value}))}
                style={{background:input,border:`1px solid ${border}`,borderRadius:7,
                  padding:"8px 12px",color:text,fontSize:13,outline:"none",
                  gridColumn:k==="description"?"span 2":""}}/>
            ))}
          </div>
          <div style={{display:"flex",gap:10,alignItems:"center"}}>
            <select value={submitForm.stack} onChange={e=>setSubmitForm(f=>({...f,stack:e.target.value}))}
              style={{background:input,border:`1px solid ${border}`,borderRadius:7,
                padding:"8px 12px",color:text,fontSize:13,outline:"none"}}>
              {["python","node","docker","conda"].map(s=><option key={s}>{s}</option>)}
            </select>
            <button onClick={submitApp}
              style={{background:"#4F8EF7",border:"none",borderRadius:7,padding:"8px 16px",
                color:"#fff",fontSize:13,fontWeight:600,cursor:"pointer"}}>Submit</button>
            {submitMsg && <span style={{fontSize:12,color:sub}}>{submitMsg}</span>}
          </div>
        </div>
      )}

      {loading && <div style={{color:sub,textAlign:"center",padding:60}}>Loading store...</div>}
      <div style={{display:"grid",gap:14,gridTemplateColumns:"repeat(auto-fill,minmax(300px,1fr))"}}>
        {apps.map(a=>(
          <AppCard key={a.id} app={a} theme={theme}
            onInstall={a=>onInstallUrl(a.github_url, a.name)}/>
        ))}
      </div>
    </div>
  )
}
