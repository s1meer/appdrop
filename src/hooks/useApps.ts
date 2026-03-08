import { useState, useEffect, useCallback } from "react"
import { api, App } from "../lib/api"

export function useApps() {
  const [apps, setApps] = useState<App[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string|null>(null)

  const refresh = useCallback(async () => {
    try { setApps(await api.listApps()); setError(null) }
    catch(e) { setError("Engine offline — is it running?") }
    finally { setLoading(false) }
  }, [])

  useEffect(() => { refresh(); const t = setInterval(refresh, 3000); return () => clearInterval(t) }, [refresh])
  return { apps, loading, error, refresh }
}

export function useWebSocket(appId: string|null, onEvent: (e:any)=>void) {
  useEffect(() => {
    if (!appId) return
    const ws = new WebSocket(`ws://127.0.0.1:8742/apps/${appId}/progress`)
    ws.onmessage = (m) => { try { onEvent(JSON.parse(m.data)) } catch {} }
    return () => ws.close()
  }, [appId])
}
