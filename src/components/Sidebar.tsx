import { App } from "../lib/api"

const NAV = [
  {id:"store",   icon:"▼",  label:"App Store"},
  {id:"myapps",  icon:"⊞",  label:"My Apps"},
  {id:"settings",icon:"⚙",  label:"Settings"},
]

const STATUS_COLOR: Record<string,string> = {
  running:"#2ECC71", ready:"#4F8EF7", error:"#E74C3C",
  installing:"#F39C12", updating:"#F39C12", stopped:"#5A6278", queued:"#5A6278"
}

interface Props {
  page: string; setPage: (p:string)=>void
  apps: App[]; theme: "dark"|"light"
}

export default function Sidebar({ page, setPage, apps, theme }: Props) {
  const bg = theme==="dark" ? "#0D0F15" : "#F0F2F8"
  const text = theme==="dark" ? "#E8EAF0" : "#1A1D2E"
  const sub = theme==="dark" ? "#5A6278" : "#8A8FA8"
  const hover = theme==="dark" ? "#1A1D2E" : "#E0E4F0"
  const active = theme==="dark" ? "#1E2235" : "#D8DCF0"
  const running = apps.filter(a=>a.status==="running").length

  return (
    <div style={{width:220,background:bg,borderRight:`1px solid ${theme==="dark"?"#1A1D2E":"#D8DCF0"}`,
      display:"flex",flexDirection:"column",flexShrink:0,height:"100vh"}}>
      {/* Logo */}
      <div style={{padding:"24px 20px 16px",borderBottom:`1px solid ${theme==="dark"?"#1A1D2E":"#D8DCF0"}`}}>
        <div style={{fontSize:22,fontWeight:900,color:text,letterSpacing:-1,display:"flex",alignItems:"center",gap:8}}>
          <img src="/icons/icon.png" width="28" height="28" style={{borderRadius:6}} />
          AppDrop
        </div>
        <div style={{fontSize:11,color:sub,marginTop:2}}>
          {running > 0 ? `${running} app${running>1?"s":""} running` : "No apps running"}
        </div>
      </div>
      {/* Nav */}
      <nav style={{flex:1,padding:"12px 8px"}}>
        {NAV.map(n => (
          <div key={n.id} onClick={()=>setPage(n.id)}
            style={{display:"flex",alignItems:"center",gap:10,padding:"10px 12px",
              borderRadius:8,cursor:"pointer",marginBottom:2,
              background: page===n.id ? active : "transparent",
              color: page===n.id ? text : sub,
              fontWeight: page===n.id ? 600 : 400, fontSize:14,
              transition:"all 0.15s"}}
            onMouseEnter={e=>(e.currentTarget.style.background=page===n.id?active:hover)}
            onMouseLeave={e=>(e.currentTarget.style.background=page===n.id?active:"transparent")}>
            <span style={{fontSize:16}}>{n.icon}</span>{n.label}
          </div>
        ))}
        {/* Running apps */}
        {apps.filter(a=>a.status==="running").length > 0 && (
          <div style={{marginTop:16}}>
            <div style={{fontSize:10,color:sub,padding:"0 12px",marginBottom:6,textTransform:"uppercase",letterSpacing:1}}>
              Running
            </div>
            {apps.filter(a=>a.status==="running").map(a=>(
              <div key={a.id} style={{display:"flex",alignItems:"center",gap:8,
                padding:"7px 12px",borderRadius:8,fontSize:12,color:text}}>
                <div style={{width:7,height:7,borderRadius:"50%",background:STATUS_COLOR[a.status],
                  boxShadow:`0 0 6px ${STATUS_COLOR[a.status]}`}}/>
                <span style={{overflow:"hidden",textOverflow:"ellipsis",whiteSpace:"nowrap"}}>{a.name}</span>
              </div>
            ))}
          </div>
        )}
      </nav>
      <div style={{padding:"12px 20px",fontSize:10,color:sub}}>v0.5.0 · AppDrop</div>
    </div>
  )
}
