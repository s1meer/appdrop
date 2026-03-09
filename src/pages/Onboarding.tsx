import { useState } from "react"
import { api } from "../lib/api"

interface Props { theme: "dark"|"light"; onComplete: () => void }

export default function Onboarding({ theme, onComplete }: Props) {
  const [step, setStep] = useState(0)
  const [sysInfo, setSysInfo] = useState<any>(null)
  const [deps, setDeps] = useState<any>(null)
  const [loading, setLoading] = useState(false)

  const bg = theme==="dark" ? "#0A0C11" : "#F4F6FF"
  const card = theme==="dark" ? "#0D0F15" : "#FFFFFF"
  const text = theme==="dark" ? "#E8EAF0" : "#1A1D2E"
  const sub  = theme==="dark" ? "#5A6278" : "#8A8FA8"
  const border = theme==="dark" ? "#1A1D2E" : "#D8DCF0"
  const panel = theme==="dark" ? "#141720" : "#F4F6FF"

  async function checkSystem() {
    setLoading(true)
    try {
      const [info, d] = await Promise.all([api.systemInfo(), api.checkDeps()])
      setSysInfo(info); setDeps(d)
    } catch { /* offline — continue anyway */ }
    setLoading(false); setStep(1)
  }

  const steps = ["Welcome", "System Check", "Ready!"]

  return (
    <div style={{
      display:"flex",alignItems:"center",justifyContent:"center",
      width:"100vw",height:"100vh",background:bg,
      fontFamily:"-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif"
    }}>
      <div style={{
        background:card,border:`1px solid ${border}`,borderRadius:16,
        padding:"40px 40px",width:500,maxWidth:"90vw",
        boxShadow:theme==="dark"?"0 24px 64px rgba(0,0,0,0.5)":"0 8px 32px rgba(0,0,0,0.12)"
      }}>
        {/* Progress dots */}
        <div style={{display:"flex",justifyContent:"center",gap:8,marginBottom:32}}>
          {steps.map((_, i) => (
            <div key={i} style={{
              width: i===step ? 24 : 8, height:8, borderRadius:4,
              background: i<step ? "#2ECC71" : i===step ? "#4F8EF7" : border,
              transition:"all 0.3s"
            }}/>
          ))}
        </div>

        {/* Step 0: Welcome */}
        {step===0 && (
          <div style={{textAlign:"center"}}>
            <div style={{fontSize:56,marginBottom:16}}>🚀</div>
            <h1 style={{color:text,fontSize:24,fontWeight:900,margin:"0 0 8px"}}>Welcome to AppDrop</h1>
            <p style={{color:sub,fontSize:14,margin:"0 0 32px",lineHeight:1.6}}>
              One-click installer for local AI apps. Let's check your system and get you ready.
            </p>
            <button onClick={checkSystem} disabled={loading} style={{
              width:"100%",padding:"13px",borderRadius:8,border:"none",
              background:"#4F8EF7",color:"#fff",fontSize:15,fontWeight:700,
              cursor:"pointer",opacity:loading?0.7:1
            }}>
              {loading ? "Checking…" : "Check My System →"}
            </button>
          </div>
        )}

        {/* Step 1: System info */}
        {step===1 && (
          <>
            <h2 style={{color:text,fontSize:18,fontWeight:800,margin:"0 0 20px"}}>Your System</h2>
            {sysInfo && (
              <div style={{display:"grid",gridTemplateColumns:"1fr 1fr",gap:8,marginBottom:20}}>
                {[
                  ["Platform",    sysInfo.platform?.toUpperCase()],
                  ["RAM",         `${sysInfo.ram_gb?.toFixed(1)} GB`],
                  ["CPU Cores",   sysInfo.cpu?.cores],
                  ["Apple Silicon", sysInfo.cpu?.is_apple_silicon ? "Yes ✓" : "No"],
                  ["Metal GPU",   sysInfo.gpu?.has_metal ? "Yes ✓" : "No"],
                  ["Free Disk",   `${sysInfo.disk_free_gb?.toFixed(0)} GB`],
                ].map(([label,val]) => (
                  <div key={label as string} style={{
                    background:panel,borderRadius:8,padding:"10px 14px",border:`1px solid ${border}`
                  }}>
                    <div style={{fontSize:10,color:sub,marginBottom:2,textTransform:"uppercase",letterSpacing:0.5}}>{label}</div>
                    <div style={{color:text,fontWeight:600,fontSize:14}}>{val}</div>
                  </div>
                ))}
              </div>
            )}
            {deps && (
              <div style={{marginBottom:20}}>
                <div style={{fontSize:11,color:sub,marginBottom:8,textTransform:"uppercase",letterSpacing:0.5}}>
                  Dependencies
                </div>
                {Object.entries(deps).map(([key, d]: any) => (
                  <div key={key} style={{
                    display:"flex",justifyContent:"space-between",alignItems:"center",
                    padding:"7px 0",borderBottom:`1px solid ${border}`,fontSize:13
                  }}>
                    <span style={{color:text}}>{d.name}</span>
                    {d.installed ? (
                      <span style={{color:"#2ECC71",fontSize:12}}>✓ {d.version?.split(" ")[0]||""}</span>
                    ) : (
                      <a href={d.install_url} target="_blank" rel="noopener noreferrer"
                        style={{color:"#E74C3C",fontSize:12,textDecoration:"none"}}>
                        ✕ Install →
                      </a>
                    )}
                  </div>
                ))}
              </div>
            )}
            <button onClick={()=>setStep(2)} style={{
              width:"100%",padding:"12px",borderRadius:8,border:"none",
              background:"#4F8EF7",color:"#fff",fontSize:14,fontWeight:700,cursor:"pointer"
            }}>
              Continue →
            </button>
          </>
        )}

        {/* Step 2: Ready */}
        {step===2 && (
          <div style={{textAlign:"center"}}>
            <div style={{fontSize:56,marginBottom:16}}>🎉</div>
            <h2 style={{color:text,fontSize:22,fontWeight:900,margin:"0 0 8px"}}>You're all set!</h2>
            <p style={{color:sub,fontSize:14,margin:"0 0 24px",lineHeight:1.6}}>
              Browse 28 local AI apps, install with one click, and launch instantly.
            </p>
            <div style={{
              background:panel,borderRadius:10,padding:"14px 16px",
              marginBottom:24,border:`1px solid ${border}`,textAlign:"left"
            }}>
              <div style={{color:sub,fontSize:11,marginBottom:6,textTransform:"uppercase",letterSpacing:0.5}}>Quick tips</div>
              <div style={{color:text,fontSize:13,lineHeight:1.7}}>
                • <kbd style={{background:border,borderRadius:4,padding:"1px 5px",fontSize:11}}>⌘K</kbd> — Quick launcher<br/>
                • <kbd style={{background:border,borderRadius:4,padding:"1px 5px",fontSize:11}}>⌘N</kbd> — Install from GitHub URL<br/>
                • <kbd style={{background:border,borderRadius:4,padding:"1px 5px",fontSize:11}}>⌘1/2/3</kbd> — Switch tabs
              </div>
            </div>
            <button onClick={()=>{ localStorage.setItem("appdrop_onboarded","1"); onComplete() }} style={{
              width:"100%",padding:"13px",borderRadius:8,border:"none",
              background:"#2ECC71",color:"#fff",fontSize:15,fontWeight:700,cursor:"pointer"
            }}>
              Open App Store →
            </button>
          </div>
        )}
      </div>
    </div>
  )
}
