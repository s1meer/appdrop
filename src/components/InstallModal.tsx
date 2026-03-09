import { useState } from "react"
import { api } from "../lib/api"

function extractGithubUrl(text: string): string | null {
  const m = text.match(/https?:\/\/github\.com\/[\w.-]+\/[\w.-]+/)
  return m ? m[0] : null
}

interface Props {
  onClose: ()=>void; onInstalled: (id:string)=>void; theme:"dark"|"light"
}

export default function InstallModal({ onClose, onInstalled, theme }: Props) {
  const [url, setUrl] = useState("")
  const [preview, setPreview] = useState<any>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState("")
  const [step, setStep] = useState<"url"|"confirm"|"installing">("url")
  const [dragging, setDragging] = useState(false)

  const bg = theme==="dark" ? "#141720" : "#FFFFFF"
  const border = theme==="dark" ? "#1E2235" : "#D8DCF0"
  const text = theme==="dark" ? "#E8EAF0" : "#1A1D2E"
  const sub = theme==="dark" ? "#5A6278" : "#8A8FA8"
  const input = theme==="dark" ? "#0D0F15" : "#F4F6FF"

  async function validate() {
    if (!url.trim()) return
    setLoading(true); setError("")
    try {
      const data = await api.validateUrl(url)
      setPreview(data); setStep("confirm")
    } catch { setError("Invalid GitHub URL or repo not found") }
    finally { setLoading(false) }
  }

  async function install() {
    setStep("installing"); setLoading(true)
    try {
      const { app_id } = await api.installApp(preview.clone_url, preview.name)
      onInstalled(app_id)
      onClose()
    } catch(e:any) { setError(e.message); setStep("confirm") }
    finally { setLoading(false) }
  }

  return (
    <div style={{position:"fixed",inset:0,background:"rgba(0,0,0,0.7)",
      display:"flex",alignItems:"center",justifyContent:"center",zIndex:100}}>
      <div style={{background:bg,border:`1px solid ${border}`,borderRadius:16,
        width:480,padding:32,boxShadow:"0 24px 80px rgba(0,0,0,0.4)"}}>
        <div style={{display:"flex",justifyContent:"space-between",alignItems:"center",marginBottom:24}}>
          <h2 style={{color:text,fontSize:18,fontWeight:700,margin:0}}>
            {step==="confirm" ? `Install ${preview?.name}` : "Install from GitHub"}
          </h2>
          <button onClick={onClose} style={{background:"none",border:"none",
            color:sub,fontSize:20,cursor:"pointer"}}>✕</button>
        </div>

        {step==="url" && <>
          <div
            onDragOver={e=>{e.preventDefault();setDragging(true)}}
            onDragLeave={()=>setDragging(false)}
            onDrop={e=>{
              e.preventDefault(); setDragging(false)
              const text = e.dataTransfer.getData("text")
              const found = extractGithubUrl(text)
              if (found) setUrl(found)
            }}
            style={{
              border:`2px dashed ${dragging?"#4F8EF7":border}`,
              borderRadius:8,padding:"10px 14px",marginBottom:8,
              background:dragging?"#4F8EF710":input,transition:"all 0.15s",
              textAlign:"center",color:dragging?"#4F8EF7":sub,fontSize:12
            }}>
            {dragging ? "Drop GitHub URL here" : "Drag a GitHub link here, or type below"}
          </div>
          <input value={url} onChange={e=>setUrl(e.target.value)}
            onKeyDown={e=>e.key==="Enter"&&validate()}
            placeholder="https://github.com/owner/repo"
            style={{width:"100%",background:input,border:`1px solid ${border}`,
              borderRadius:8,padding:"12px 14px",color:text,fontSize:14,
              outline:"none",boxSizing:"border-box"}}/>
          {error && <p style={{color:"#E74C3C",fontSize:12,marginTop:8}}>{error}</p>}
          <button onClick={validate} disabled={loading}
            style={{marginTop:16,width:"100%",background:"#4F8EF7",border:"none",
              borderRadius:8,padding:"12px",color:"#fff",fontSize:14,fontWeight:600,
              cursor:"pointer",opacity:loading?0.6:1}}>
            {loading ? "Checking..." : "Preview →"}
          </button>
        </>}

        {step==="confirm" && preview && <>
          <div style={{background:input,borderRadius:10,padding:16,marginBottom:20}}>
            <div style={{color:text,fontWeight:600,marginBottom:4}}>{preview.name}</div>
            <div style={{color:sub,fontSize:13,marginBottom:8}}>{preview.description||"No description"}</div>
            <div style={{display:"flex",gap:12,fontSize:12}}>
              <span style={{color:"#4F8EF7"}}>⬡ {preview.stack||preview.language||"unknown"}</span>
              <span style={{color:sub}}>⭐ {(preview.stars||0).toLocaleString()}</span>
              <span style={{color:sub}}>@{preview.owner}/{preview.repo}</span>
            </div>
          </div>
          <div style={{display:"flex",gap:10}}>
            <button onClick={()=>setStep("url")}
              style={{flex:1,background:"none",border:`1px solid ${border}`,borderRadius:8,
                padding:"11px",color:sub,fontSize:14,cursor:"pointer"}}>← Back</button>
            <button onClick={install}
              style={{flex:2,background:"#4F8EF7",border:"none",borderRadius:8,
                padding:"11px",color:"#fff",fontSize:14,fontWeight:600,cursor:"pointer"}}>
              Install Now ↓
            </button>
          </div>
        </>}

        {step==="installing" && (
          <div style={{textAlign:"center",padding:"20px 0"}}>
            <div style={{fontSize:32,marginBottom:12}}>⬇</div>
            <div style={{color:text,fontWeight:600}}>Installing {preview?.name}...</div>
            <div style={{color:sub,fontSize:13,marginTop:6}}>
              Track progress in My Apps
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
