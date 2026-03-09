import { RegistryApp } from "../lib/api"

const COMPAT_COLOR: Record<string, string> = {
  excellent: "#2ECC71", ok: "#F39C12", needs_gpu: "#FF9800", too_heavy: "#E74C3C"
}

interface Props {
  app: RegistryApp
  theme: "dark"|"light"
  onInstall: (a: RegistryApp) => void
  onClose: () => void
}

export default function AppDetail({ app, theme, onInstall, onClose }: Props) {
  const bg    = theme==="dark" ? "#0A0C11" : "#F4F6FF"
  const card  = theme==="dark" ? "#0D0F15" : "#FFFFFF"
  const text  = theme==="dark" ? "#E8EAF0" : "#1A1D2E"
  const sub   = theme==="dark" ? "#5A6278" : "#8A8FA8"
  const border = theme==="dark" ? "#1A1D2E" : "#D8DCF0"
  const panel = theme==="dark" ? "#141720" : "#F4F6FF"

  const compatColor = COMPAT_COLOR[app.compatibility||""] || sub

  return (
    <div style={{
      position:"fixed",inset:0,background:"rgba(0,0,0,0.75)",
      display:"flex",alignItems:"center",justifyContent:"center",zIndex:200
    }} onClick={e=>e.target===e.currentTarget&&onClose()}>
      <div style={{
        background:card,borderRadius:16,width:680,maxWidth:"92vw",
        maxHeight:"88vh",overflow:"hidden",display:"flex",flexDirection:"column",
        border:`1px solid ${border}`,boxShadow:"0 32px 80px rgba(0,0,0,0.5)"
      }}>
        {/* Header */}
        <div style={{padding:"24px 28px 18px",borderBottom:`1px solid ${border}`,flexShrink:0}}>
          <div style={{display:"flex",justifyContent:"space-between",alignItems:"flex-start"}}>
            <div style={{flex:1,minWidth:0}}>
              <div style={{fontSize:22,fontWeight:800,color:text,marginBottom:4}}>{app.name}</div>
              <div style={{color:sub,fontSize:13,lineHeight:1.5}}>{app.description}</div>
            </div>
            <button onClick={onClose} style={{
              background:"none",border:"none",color:sub,fontSize:20,cursor:"pointer",
              marginLeft:16,flexShrink:0,padding:4
            }}>✕</button>
          </div>
          <div style={{display:"flex",gap:10,marginTop:14,flexWrap:"wrap",alignItems:"center"}}>
            <span style={{color:"#F39C12",fontSize:13,fontWeight:600}}>
              ⭐ {(app.stars_approx/1000).toFixed(1)}k
            </span>
            <span style={{
              color:sub,fontSize:12,background:panel,borderRadius:6,
              padding:"3px 10px",border:`1px solid ${border}`
            }}>{app.stack}</span>
            {app.compatibility && (
              <span style={{
                color:compatColor,fontSize:12,fontWeight:600,
                background:`${compatColor}18`,borderRadius:6,padding:"3px 10px",
                border:`1px solid ${compatColor}40`
              }}>
                {app.compatibility.replace("_"," ")}
              </span>
            )}
            {app.verified && <span style={{color:"#4F8EF7",fontSize:12}}>✓ verified</span>}
          </div>
          {app.tags.length > 0 && (
            <div style={{display:"flex",gap:6,flexWrap:"wrap",marginTop:10}}>
              {app.tags.map(t=>(
                <span key={t} style={{
                  fontSize:11,color:sub,background:panel,borderRadius:4,
                  padding:"2px 8px",border:`1px solid ${border}`
                }}>{t}</span>
              ))}
            </div>
          )}
        </div>

        {/* Stats row */}
        <div style={{
          padding:"14px 28px",borderBottom:`1px solid ${border}`,
          display:"flex",gap:24,flexShrink:0
        }}>
          {[
            ["Default Port", app.default_port],
            ["Min RAM",      `${(app as any).min_ram_gb || 4} GB`],
            ["Stack",        app.stack],
          ].map(([label,val])=>(
            <div key={label as string}>
              <div style={{fontSize:10,color:sub,marginBottom:2,textTransform:"uppercase",letterSpacing:0.5}}>{label}</div>
              <div style={{color:text,fontWeight:600,fontSize:14,textTransform:"capitalize"}}>{val}</div>
            </div>
          ))}
        </div>

        {/* Body */}
        <div style={{flex:1,overflow:"auto",padding:"20px 28px"}}>
          {/* Screenshot placeholder */}
          <div style={{
            background:panel,borderRadius:10,border:`2px dashed ${border}`,
            height:120,display:"flex",alignItems:"center",justifyContent:"center",
            marginBottom:20,color:sub,fontSize:13
          }}>
            📸 Screenshots coming soon
          </div>
          {/* GitHub link */}
          <a href={app.github_url} target="_blank" rel="noopener noreferrer"
            style={{
              display:"inline-flex",alignItems:"center",gap:6,
              color:"#4F8EF7",fontSize:13,textDecoration:"none",
              padding:"8px 14px",border:`1px solid #4F8EF740`,
              borderRadius:7,background:"#4F8EF710"
            }}>
            <svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor">
              <path d="M12 0C5.37 0 0 5.37 0 12c0 5.3 3.44 9.8 8.2 11.4.6.1.82-.26.82-.58v-2.2c-3.34.72-4.04-1.42-4.04-1.42-.54-1.38-1.33-1.74-1.33-1.74-1.09-.74.08-.73.08-.73 1.2.08 1.84 1.24 1.84 1.24 1.07 1.83 2.8 1.3 3.49 1 .1-.78.42-1.3.76-1.6-2.67-.3-5.47-1.33-5.47-5.93 0-1.31.47-2.38 1.24-3.22-.14-.3-.54-1.52.1-3.18 0 0 1-.32 3.3 1.23a11.5 11.5 0 0 1 6 0c2.28-1.55 3.28-1.23 3.28-1.23.65 1.66.24 2.88.12 3.18.77.84 1.24 1.91 1.24 3.22 0 4.61-2.8 5.63-5.48 5.92.42.36.81 1.1.81 2.22v3.29c0 .32.22.7.83.58C20.57 21.8 24 17.3 24 12c0-6.63-5.37-12-12-12z"/>
            </svg>
            View on GitHub →
          </a>
        </div>

        {/* Footer */}
        <div style={{
          padding:"16px 28px",borderTop:`1px solid ${border}`,
          display:"flex",gap:10,flexShrink:0
        }}>
          <button onClick={onClose} style={{
            flex:1,padding:"11px",borderRadius:8,background:"none",
            border:`1px solid ${border}`,color:sub,cursor:"pointer",fontSize:14
          }}>Close</button>
          <button onClick={()=>{onInstall(app);onClose()}} disabled={app.installed} style={{
            flex:2,padding:"11px",borderRadius:8,border:"none",
            background:app.installed?"#1A1D2E":"#4F8EF7",
            color:app.installed?sub:"#fff",fontSize:14,fontWeight:700,
            cursor:app.installed?"default":"pointer"
          }}>
            {app.installed ? "Already Installed ✓" : "Install Now →"}
          </button>
        </div>
      </div>
    </div>
  )
}
