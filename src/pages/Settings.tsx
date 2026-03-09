import { useState, useEffect } from "react"
import { AuthUser } from "../hooks/useAuth"
import { api } from "../lib/api"

interface Props {
  theme: "dark"|"light"
  setTheme: (t:"dark"|"light")=>void
  user?: AuthUser | null
  onLogout?: () => void
}

export default function Settings({ theme, setTheme, user, onLogout }: Props) {
  const [analytics, setAnalytics] = useState<any>(null)
  const text   = theme==="dark" ? "#E8EAF0" : "#1A1D2E"
  const sub    = theme==="dark" ? "#5A6278" : "#8A8FA8"
  const bg2    = theme==="dark" ? "#141720" : "#FFFFFF"
  const border = theme==="dark" ? "#1E2235" : "#D8DCF0"

  useEffect(() => {
    api.analytics().then(setAnalytics).catch(() => {})
  }, [])

  const Row = ({label,children}:{label:string,children:React.ReactNode}) => (
    <div style={{display:"flex",justifyContent:"space-between",alignItems:"center",
      padding:"16px 0",borderBottom:`1px solid ${border}`}}>
      <span style={{color:text,fontSize:14}}>{label}</span>
      {children}
    </div>
  )

  return (
    <div style={{flex:1,overflow:"auto",padding:32,maxWidth:600}}>
      <h1 style={{color:text,fontSize:22,fontWeight:800,margin:"0 0 24px"}}>Settings</h1>

      {/* Profile card */}
      {user && (
        <div style={{background:bg2,border:`1px solid ${border}`,borderRadius:12,
          padding:20,marginBottom:20,display:"flex",alignItems:"center",gap:16}}>
          {user.avatar_url ? (
            <img src={user.avatar_url} width={52} height={52}
              style={{borderRadius:"50%",objectFit:"cover",flexShrink:0}} />
          ) : (
            <div style={{width:52,height:52,borderRadius:"50%",background:"#4F8EF7",
              display:"flex",alignItems:"center",justifyContent:"center",
              color:"#fff",fontSize:22,fontWeight:700,flexShrink:0}}>
              {(user.name||user.email||"?")[0].toUpperCase()}
            </div>
          )}
          <div style={{flex:1,minWidth:0}}>
            <div style={{fontSize:16,fontWeight:700,color:text,marginBottom:2}}>
              {user.name || "Guest"}
            </div>
            <div style={{fontSize:12,color:sub}}>{user.email}</div>
            <div style={{fontSize:11,color:sub,marginTop:2,textTransform:"capitalize"}}>
              {user.isGuest ? "Guest session" : `via ${user.provider}`}
            </div>
          </div>
          {!user.isGuest && (
            <button onClick={onLogout}
              style={{background:"none",border:`1px solid ${border}`,borderRadius:7,
                padding:"7px 14px",color:sub,fontSize:12,cursor:"pointer"}}>
              Sign out
            </button>
          )}
        </div>
      )}

      <div style={{background:bg2,border:`1px solid ${border}`,borderRadius:12,padding:"0 20px"}}>
        <Row label="Theme">
          <div style={{display:"flex",gap:8}}>
            {(["dark","light"] as const).map(t=>(
              <button key={t} onClick={()=>setTheme(t)}
                style={{background:theme===t?"#4F8EF7":"none",border:`1px solid ${theme===t?"#4F8EF7":border}`,
                  borderRadius:6,padding:"5px 14px",color:theme===t?"#fff":sub,
                  fontSize:12,cursor:"pointer",textTransform:"capitalize"}}>{t}</button>
            ))}
          </div>
        </Row>
        <Row label="Engine URL">
          <span style={{color:sub,fontSize:12,fontFamily:"monospace"}}>http://127.0.0.1:8742</span>
        </Row>
        <Row label="App Storage">
          <span style={{color:sub,fontSize:12,fontFamily:"monospace"}}>~/.appdrop/apps/</span>
        </Row>
        <Row label="Port Range">
          <span style={{color:sub,fontSize:12,fontFamily:"monospace"}}>7800 – 7900</span>
        </Row>
        <Row label="Version">
          <span style={{color:"#4F8EF7",fontSize:12}}>v0.7.0</span>
        </Row>
      </div>
      {analytics && (
        <div style={{marginTop:24,background:bg2,border:`1px solid ${border}`,borderRadius:12,padding:20}}>
          <div style={{color:text,fontWeight:600,marginBottom:14,fontSize:14}}>Your AppDrop Stats</div>
          <div style={{display:"grid",gridTemplateColumns:"repeat(3,1fr)",gap:10}}>
            {[
              ["Total Launches", analytics.total_launches ?? 0],
              ["Installs Today", analytics.installs_today ?? 0],
              ["Total Installs", analytics.total_installs ?? 0],
            ].map(([label,val])=>(
              <div key={label as string} style={{background:theme==="dark"?"#0D0F15":"#F4F6FF",
                borderRadius:8,padding:"10px 14px",border:`1px solid ${border}`}}>
                <div style={{fontSize:10,color:sub,marginBottom:4,textTransform:"uppercase",letterSpacing:0.5}}>{label}</div>
                <div style={{color:text,fontWeight:700,fontSize:20}}>{val}</div>
              </div>
            ))}
          </div>
          {analytics.top_apps?.length > 0 && (
            <div style={{marginTop:14}}>
              <div style={{fontSize:11,color:sub,marginBottom:6,textTransform:"uppercase",letterSpacing:0.5}}>Top Apps</div>
              {analytics.top_apps.slice(0,3).map((a: any) => (
                <div key={a.id} style={{display:"flex",justifyContent:"space-between",
                  padding:"5px 0",borderBottom:`1px solid ${border}`,fontSize:13}}>
                  <span style={{color:text}}>{a.id}</span>
                  <span style={{color:sub}}>{a.launches} launches</span>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      <div style={{marginTop:24,background:bg2,border:`1px solid ${border}`,borderRadius:12,padding:20}}>
        <div style={{color:text,fontWeight:600,marginBottom:8,fontSize:14}}>Start Engine</div>
        <div style={{color:sub,fontSize:12,marginBottom:10}}>Run this in your terminal to start the backend:</div>
        <div style={{background:theme==="dark"?"#0D0F15":"#F4F6FF",borderRadius:7,
          padding:"10px 14px",fontFamily:"monospace",fontSize:12,color:"#4F8EF7"}}>
          cd ~/Downloads/appdrop/engine && python3 -m uvicorn main:app --port 8742
        </div>
      </div>
    </div>
  )
}
