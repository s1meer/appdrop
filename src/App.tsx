import { useState, useEffect } from "react"
import Sidebar from "./components/Sidebar"
import InstallModal from "./components/InstallModal"
import MyApps from "./pages/MyApps"
import AppStore from "./pages/AppStore"
import Settings from "./pages/Settings"
import Auth from "./pages/Auth"
import Onboarding from "./pages/Onboarding"
import AppDetail from "./pages/AppDetail"
import ToastContainer from "./components/Toast"
import { useApps } from "./hooks/useApps"
import { useAuth } from "./hooks/useAuth"
import { useToast } from "./hooks/useToast"
import { api, RegistryApp } from "./lib/api"

export default function App() {
  const [page, setPage] = useState<string>("store")
  const [theme, setTheme] = useState<"dark"|"light">("dark")
  const [showInstall, setShowInstall] = useState(false)
  const [selectedApp, setSelectedApp] = useState<RegistryApp | null>(null)
  const { apps, loading, error, refresh } = useApps()
  const { user, isLoggedIn, login, logout } = useAuth()
  const { toasts, addToast, removeToast } = useToast()
  const [authDone, setAuthDone] = useState(isLoggedIn)
  const [onboarded, setOnboarded] = useState(!!localStorage.getItem("appdrop_onboarded"))

  const bg = theme==="dark" ? "#0A0C11" : "#F4F6FF"

  // Keyboard shortcuts
  useEffect(() => {
    function onKey(e: KeyboardEvent) {
      if (!(e.metaKey || e.ctrlKey)) return
      if (e.key === "k") { e.preventDefault(); setShowInstall(true) }
      if (e.key === "n") { e.preventDefault(); setShowInstall(true) }
      if (e.key === "1") { e.preventDefault(); setPage("store") }
      if (e.key === "2") { e.preventDefault(); setPage("myapps") }
      if (e.key === "3") { e.preventDefault(); setPage("settings") }
    }
    window.addEventListener("keydown", onKey)
    return () => window.removeEventListener("keydown", onKey)
  }, [])

  async function handleInstall(app: RegistryApp) {
    try {
      await api.installApp(app.github_url, app.name)
      refresh()
      setPage("myapps")
      addToast(`Installing ${app.name}…`, "info")
    } catch { addToast("Install failed", "error") }
  }

  async function handleInstallUrl(url: string, name: string) {
    try {
      await api.installApp(url, name)
      refresh(); setPage("myapps")
      addToast(`Installing ${name}…`, "info")
    } catch { addToast("Install failed", "error") }
  }

  if (!authDone) {
    return <Auth theme={theme} onAuth={() => setAuthDone(true)} />
  }

  if (!onboarded) {
    return <Onboarding theme={theme} onComplete={() => setOnboarded(true)} />
  }

  return (
    <div style={{display:"flex",height:"100vh",background:bg,
      fontFamily:"-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif",overflow:"hidden"}}>
      <Sidebar page={page} setPage={setPage} apps={apps} theme={theme} user={user}
        onLogout={() => { logout(); setAuthDone(false) }}/>
      {page==="store"  && <AppStore theme={theme} onInstallUrl={handleInstallUrl}
        onSelectApp={setSelectedApp}/>}
      {page==="myapps" && <MyApps apps={apps} loading={loading} error={error}
        theme={theme} onInstall={()=>setShowInstall(true)} refresh={refresh}/>}
      {page==="settings" && <Settings theme={theme} setTheme={setTheme}
        user={user} onLogout={() => { logout(); setAuthDone(false) }}/>}
      {showInstall && <InstallModal theme={theme}
        onClose={()=>setShowInstall(false)}
        onInstalled={(id)=>{ refresh(); setPage("myapps"); addToast("Install started!", "success") }}/>}
      {selectedApp && <AppDetail app={selectedApp} theme={theme}
        onInstall={handleInstall} onClose={()=>setSelectedApp(null)}/>}
      <ToastContainer toasts={toasts} onRemove={removeToast}/>
    </div>
  )
}
