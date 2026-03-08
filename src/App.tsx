import { useState } from "react"
import Sidebar from "./components/Sidebar"
import InstallModal from "./components/InstallModal"
import MyApps from "./pages/MyApps"
import AppStore from "./pages/AppStore"
import Settings from "./pages/Settings"
import { useApps } from "./hooks/useApps"
import { api } from "./lib/api"

export default function App() {
  const [page, setPage] = useState<string>("store")
  const [theme, setTheme] = useState<"dark"|"light">("dark")
  const [showInstall, setShowInstall] = useState(false)
  const [installUrl, setInstallUrl] = useState("")
  const { apps, loading, error, refresh } = useApps()

  const bg = theme==="dark" ? "#0A0C11" : "#F4F6FF"

  async function handleInstallUrl(url: string, name: string) {
    setInstallUrl(url)
    try {
      const { app_id } = await api.installApp(url, name)
      refresh(); setPage("myapps")
    } catch {}
  }

  return (
    <div style={{display:"flex",height:"100vh",background:bg,
      fontFamily:"-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif",overflow:"hidden"}}>
      <Sidebar page={page} setPage={setPage} apps={apps} theme={theme}/>
      {page==="store"  && <AppStore  theme={theme} onInstallUrl={handleInstallUrl}/>}
      {page==="myapps" && <MyApps   apps={apps} loading={loading} error={error}
                                     theme={theme} onInstall={()=>setShowInstall(true)} refresh={refresh}/>}
      {page==="settings" && <Settings theme={theme} setTheme={setTheme}/>}
      {showInstall && <InstallModal theme={theme}
        onClose={()=>setShowInstall(false)}
        onInstalled={()=>{ refresh(); setPage("myapps") }}/>}
    </div>
  )
}
