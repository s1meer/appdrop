'use client'
import { useEffect, useState } from 'react'

interface App { id:string; name:string; status:string; stack:string; port:number|null }
interface RegApp { id:string; name:string; description:string; stars_approx:number; tags:string[] }

export default function Home() {
  const [apps, setApps] = useState<App[]>([])
  const [registry, setRegistry] = useState<RegApp[]>([])
  const [tab, setTab] = useState<'store'|'myapps'>('store')
  const [url, setUrl] = useState('')
  const [installing, setInstalling] = useState(false)
  const [msg, setMsg] = useState('')
  const ENGINE = 'http://127.0.0.1:8742'

  useEffect(() => {
    fetch(`${ENGINE}/apps`).then(r=>r.json()).then(d=>setApps(d.apps)).catch(()=>{})
    fetch(`${ENGINE}/registry`).then(r=>r.json()).then(d=>setRegistry(d.apps)).catch(()=>{})
    const t = setInterval(() => {
      fetch(`${ENGINE}/apps`).then(r=>r.json()).then(d=>setApps(d.apps)).catch(()=>{})
    }, 3000)
    return () => clearInterval(t)
  }, [])

  async function install(github_url: string, name?: string) {
    setInstalling(true); setMsg('Installing...')
    try {
      const r = await fetch(`${ENGINE}/apps/install`, {method:'POST',
        headers:{'Content-Type':'application/json'},
        body: JSON.stringify({github_url, name})})
      const d = await r.json()
      setMsg(`✅ Installing! (id: ${d.app_id})`); setTab('myapps')
      setTimeout(() => fetch(`${ENGINE}/apps`).then(r=>r.json()).then(d=>setApps(d.apps)), 1000)
    } catch { setMsg('❌ Failed') }
    finally { setInstalling(false) }
  }

  const s: Record<string,string> = {
    running:'#2ECC71',ready:'#4F8EF7',error:'#E74C3C',
    installing:'#F39C12',stopped:'#5A6278',queued:'#5A6278'
  }

  return (
    <div style={{maxWidth:1100,margin:'0 auto',padding:'24px 20px',color:'#E8EAF0'}}>
      {/* Header */}
      <div style={{display:'flex',justifyContent:'space-between',alignItems:'center',marginBottom:28}}>
        <div style={{fontSize:24,fontWeight:900}}>AppDrop <span style={{color:'#4F8EF7'}}>▼</span></div>
        <div style={{display:'flex',gap:8}}>
          {(['store','myapps'] as const).map(t=>(
            <button key={t} onClick={()=>setTab(t)}
              style={{background:tab===t?'#4F8EF7':'none',border:'1px solid',
                borderColor:tab===t?'#4F8EF7':'#1E2235',borderRadius:7,
                padding:'7px 16px',color:tab===t?'#fff':'#5A6278',fontSize:13,cursor:'pointer'}}>
              {t==='store'?'App Store':'My Apps'}
            </button>
          ))}
        </div>
      </div>

      {tab==='store' && <>
        {/* URL install bar */}
        <div style={{display:'flex',gap:10,marginBottom:24}}>
          <input value={url} onChange={e=>setUrl(e.target.value)}
            placeholder="https://github.com/owner/repo"
            style={{flex:1,background:'#141720',border:'1px solid #1E2235',borderRadius:8,
              padding:'10px 14px',color:'#E8EAF0',fontSize:14,outline:'none'}}/>
          <button onClick={()=>install(url)} disabled={installing||!url}
            style={{background:'#4F8EF7',border:'none',borderRadius:8,padding:'10px 20px',
              color:'#fff',fontSize:14,fontWeight:600,cursor:'pointer',opacity:installing?0.6:1}}>
            {installing?'Installing...':'Install ↓'}
          </button>
        </div>
        {msg && <div style={{marginBottom:16,color:'#5A6278',fontSize:13}}>{msg}</div>}

        {/* Registry grid */}
        <div style={{display:'grid',gap:14,gridTemplateColumns:'repeat(auto-fill,minmax(280px,1fr))'}}>
          {registry.map(a=>(
            <div key={a.id} style={{background:'#141720',border:'1px solid #1E2235',
              borderRadius:12,padding:18}}>
              <div style={{fontWeight:700,marginBottom:6}}>{a.name}</div>
              <div style={{color:'#5A6278',fontSize:12,marginBottom:10,lineHeight:1.5}}>
                {a.description.slice(0,80)}...
              </div>
              <div style={{display:'flex',justifyContent:'space-between',alignItems:'center'}}>
                <span style={{color:'#F39C12',fontSize:11}}>⭐ {(a.stars_approx/1000).toFixed(1)}k</span>
                <button onClick={()=>install(`https://github.com/${a.id}`, a.name)}
                  style={{background:'#4F8EF7',border:'none',borderRadius:6,padding:'5px 12px',
                    color:'#fff',fontSize:11,fontWeight:600,cursor:'pointer'}}>Install</button>
              </div>
            </div>
          ))}
        </div>
      </>}

      {tab==='myapps' && (
        <div>
          {apps.length===0 ? (
            <div style={{textAlign:'center',paddingTop:80,color:'#5A6278'}}>
              No apps installed. Browse the store!
            </div>
          ) : (
            <div style={{display:'grid',gap:12,gridTemplateColumns:'repeat(auto-fill,minmax(320px,1fr))'}}>
              {apps.map(a=>(
                <div key={a.id} style={{background:'#141720',border:'1px solid #1E2235',
                  borderRadius:12,padding:18}}>
                  <div style={{display:'flex',justifyContent:'space-between',alignItems:'center',marginBottom:8}}>
                    <span style={{fontWeight:700}}>{a.name}</span>
                    <div style={{display:'flex',alignItems:'center',gap:6}}>
                      <div style={{width:7,height:7,borderRadius:'50%',background:s[a.status]||'#5A6278'}}/>
                      <span style={{color:'#5A6278',fontSize:12}}>{a.status}</span>
                    </div>
                  </div>
                  {a.port && <div style={{color:'#4F8EF7',fontSize:12,marginBottom:8}}>
                    <a href={`http://localhost:${a.port}`} target="_blank" rel="noreferrer"
                      style={{color:'#4F8EF7'}}>localhost:{a.port} ↗</a>
                  </div>}
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  )
}
