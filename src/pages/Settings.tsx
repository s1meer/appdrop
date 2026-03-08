interface Props { theme:"dark"|"light"; setTheme:(t:"dark"|"light")=>void }

export default function Settings({ theme, setTheme }: Props) {
  const text = theme==="dark" ? "#E8EAF0" : "#1A1D2E"
  const sub  = theme==="dark" ? "#5A6278" : "#8A8FA8"
  const bg2  = theme==="dark" ? "#141720" : "#FFFFFF"
  const border = theme==="dark" ? "#1E2235" : "#D8DCF0"

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
          <span style={{color:"#4F8EF7",fontSize:12}}>v0.4.0</span>
        </Row>
      </div>
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
