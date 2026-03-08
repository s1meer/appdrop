import { useState } from "react"
import { App, api } from "../lib/api"
import { useWebSocket } from "../hooks/useApps"

const STATUS_COLOR: Record<string,string> = {
  running:"#2ECC71", ready:"#4F8EF7", error:"#E74C3C",
  installing:"#F39C12", updating:"#F39C12", stopped:"#5A6278", queued:"#5A6278"
}
const STACK_ICON: Record<string,string> = {
  python:"🐍", node:"💚", docker:"🐳", conda:"🅒", unknown:"?"
}

interface Props { apps: App[]; loading: boolean; error: string|null
  theme: "dark"|"light"; onInstall:()=>void; refresh:()=>void }

function ProgressBar({pct,color}:{pct:number,color:string}) {
  return <div style={{height:3,background:"rgba(255,255,255,0.1)",borderRadius:2,overflow:"hidden",marginTop:8}}>
    <div style={{height:"100%",width:`${pct}%`,background:color,transition:"width 0.4s",borderRadius:2}}/>
  </div>
}

function AppCard({app,theme,refresh}:{app:App,theme:"dark"|"light",refresh:()=>void}) {
  const [logs, setLogs] = useState<string[]>([])
  const [showLogs, setShowLogs] = useState(false)
  const [busy, setBusy] = useState(false)
  const bg = theme==="dark" ? "#141720" : "#FFFFFF"
  const border = theme==="dark" ? "#1E2235" : "#D8DCF0"
  const text = theme==="dark" ? "#E8EAF0" : "#1A1D2E"
  const sub = theme==="dark" ? "#5A6278" : "#8A8FA8"
  const color = STATUS_COLOR[app.status] ?? "#5A6278"

  useWebSocket(
    app.status==="installing"||app.status==="updating" ? app.id : null,
    () => refresh()
  )

  async function action(fn: ()=>Promise<any>) {
    setBusy(true); try { await fn(); refresh() } catch{} finally { setBusy(false) }
  }

  async function viewLogs() {
    const d = await api.getLogs(app.id)
    setLogs(d.logs); setShowLogs(true)
  }

  return (
    <div style={{background:bg,border:`1px solid ${border}`,borderRadius:12,padding:20,
      transition:"border-color 0.2s"}}
      onMouseEnter={e=>(e.currentTarget.style.borderColor="#4F8EF7")}
      onMouseLeave={e=>(e.currentTarget.style.borderColor=border)}>
      <div style={{display:"flex",justifyContent:"space-between",alignItems:"flex-start"}}>
        <div style={{flex:1,minWidth:0}}>
          <div style={{display:"flex",alignItems:"center",gap:8,marginBottom:4}}>
            <span style={{fontSize:18}}>{STACK_ICON[app.stack]||"?"}</span>
            <span style={{color:text,fontWeight:700,fontSize:15,
              overflow:"hidden",textOverflow:"ellipsis",whiteSpace:"nowrap"}}>{app.name}</span>
          </div>
          <div style={{display:"flex",alignItems:"center",gap:6}}>
            <div style={{width:7,height:7,borderRadius:"50%",background:color,
              boxShadow:app.status==="running"?`0 0 8px ${color}`:"none",flexShrink:0}}/>
            <span style={{color:sub,fontSize:12,textTransform:"capitalize"}}>{app.status}</span>
            {app.port && <span style={{color:"#4F8EF7",fontSize:12}}>· :{app.port}</span>}
          </div>
        </div>
        <div style={{display:"flex",gap:6,flexShrink:0}}>
          {app.status==="running" && app.port && (
            <button onClick={()=>window.open(`http://localhost:${app.port}`)}
              style={{background:"#2ECC71",border:"none",borderRadius:6,padding:"5px 10px",
                color:"#fff",fontSize:12,cursor:"pointer",fontWeight:600}}>Open ↗</button>
          )}
          {app.status==="ready" && (
            <button onClick={()=>action(()=>api.launchApp(app.id))} disabled={busy}
              style={{background:"#4F8EF7",border:"none",borderRadius:6,padding:"5px 10px",
                color:"#fff",fontSize:12,cursor:"pointer",fontWeight:600}}>Launch</button>
          )}
          {app.status==="running" && (
            <button onClick={()=>action(()=>api.stopApp(app.id))} disabled={busy}
              style={{background:"none",border:`1px solid ${border}`,borderRadius:6,
                padding:"5px 10px",color:sub,fontSize:12,cursor:"pointer"}}>Stop</button>
          )}
          {(app.status==="ready"||app.status==="stopped"||app.status==="error") && (
            <button onClick={()=>action(()=>api.updateApp(app.id))} disabled={busy}
              style={{background:"none",border:`1px solid ${border}`,borderRadius:6,
                padding:"5px 10px",color:sub,fontSize:12,cursor:"pointer"}} title="Update">↑</button>
          )}
          <button onClick={viewLogs}
            style={{background:"none",border:`1px solid ${border}`,borderRadius:6,
              padding:"5px 10px",color:sub,fontSize:12,cursor:"pointer"}}>Logs</button>
          <button onClick={()=>action(()=>api.deleteApp(app.id))} disabled={busy}
            style={{background:"none",border:`1px solid ${border}`,borderRadius:6,
              padding:"5px 10px",color:"#E74C3C",fontSize:12,cursor:"pointer"}}>✕</button>
        </div>
      </div>
      {(app.status==="installing"||app.status==="updating") && (
        <div style={{marginTop:10}}>
          <div style={{display:"flex",justifyContent:"space-between"}}>
            <span style={{color:sub,fontSize:11}}>{app.install_label}</span>
            <span style={{color:sub,fontSize:11}}>{app.install_pct}%</span>
          </div>
          <ProgressBar pct={app.install_pct} color={color}/>
        </div>
      )}
      {app.status==="error" && app.error_message && (
        <div style={{marginTop:8,background:"rgba(231,76,60,0.1)",borderRadius:6,
          padding:"6px 10px",color:"#E74C3C",fontSize:11}}>{app.error_message.slice(0,120)}</div>
      )}
      {showLogs && (
        <div style={{marginTop:12,background:theme==="dark"?"#0D0F15":"#F4F6FF",
          borderRadius:8,padding:12,maxHeight:200,overflow:"auto"}}>
          <div style={{display:"flex",justifyContent:"space-between",marginBottom:8}}>
            <span style={{color:sub,fontSize:11,fontWeight:600}}>LOGS</span>
            <button onClick={()=>setShowLogs(false)}
              style={{background:"none",border:"none",color:sub,fontSize:11,cursor:"pointer"}}>close</button>
          </div>
          {logs.map((l,i)=>(
            <div key={i} style={{fontFamily:"monospace",fontSize:11,color:sub,
              lineHeight:1.6,borderBottom:`1px solid ${border}`,padding:"2px 0"}}>{l}</div>
          ))}
        </div>
      )}
    </div>
  )
}

export default function MyApps({ apps, loading, error, theme, onInstall, refresh }: Props) {
  const text = theme==="dark" ? "#E8EAF0" : "#1A1D2E"
  const sub  = theme==="dark" ? "#5A6278" : "#8A8FA8"

  return (
    <div style={{flex:1,overflow:"auto",padding:32}}>
      <div style={{display:"flex",justifyContent:"space-between",alignItems:"center",marginBottom:24}}>
        <div>
          <h1 style={{color:text,fontSize:22,fontWeight:800,margin:0}}>My Apps</h1>
          <p style={{color:sub,fontSize:13,margin:"4px 0 0"}}>{apps.length} installed</p>
        </div>
        <button onClick={onInstall}
          style={{background:"#4F8EF7",border:"none",borderRadius:8,padding:"10px 18px",
            color:"#fff",fontSize:14,fontWeight:600,cursor:"pointer"}}>+ Install App</button>
      </div>
      {loading && <div style={{color:sub,textAlign:"center",paddingTop:60}}>Loading...</div>}
      {error  && <div style={{color:"#E74C3C",textAlign:"center",paddingTop:60}}>{error}</div>}
      {!loading && !error && apps.length===0 && (
        <div style={{textAlign:"center",paddingTop:80}}>
          <div style={{fontSize:48,marginBottom:16}}>▼</div>
          <div style={{color:text,fontWeight:600,marginBottom:8}}>No apps installed yet</div>
          <div style={{color:sub,fontSize:13,marginBottom:24}}>Browse the App Store or paste a GitHub URL</div>
          <button onClick={onInstall}
            style={{background:"#4F8EF7",border:"none",borderRadius:8,padding:"11px 24px",
              color:"#fff",fontSize:14,fontWeight:600,cursor:"pointer"}}>Browse App Store</button>
        </div>
      )}
      <div style={{display:"grid",gap:14,gridTemplateColumns:"repeat(auto-fill,minmax(400px,1fr))"}}>
        {apps.map(a=><AppCard key={a.id} app={a} theme={theme} refresh={refresh}/>)}
      </div>
    </div>
  )
}
