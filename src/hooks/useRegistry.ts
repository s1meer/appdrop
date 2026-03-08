import { useState, useEffect, useRef } from "react"
import { api, RegistryApp } from "../lib/api"

export function useRegistry(filters?: {tag?:string,stack?:string,q?:string}) {
  const [apps, setApps] = useState<RegistryApp[]>([])
  const [loading, setLoading] = useState(true)
  const retryRef = useRef<ReturnType<typeof setTimeout> | null>(null)

  useEffect(() => {
    let cancelled = false

    function clearRetry() {
      if (retryRef.current) {
        clearTimeout(retryRef.current)
        retryRef.current = null
      }
    }

    async function fetchWithRetry() {
      setLoading(true)
      try {
        const result = await api.registry(filters)
        if (!cancelled) {
          setApps(result)
          setLoading(false)
        }
      } catch {
        if (!cancelled) {
          // Engine not up yet — retry in 5 s
          retryRef.current = setTimeout(fetchWithRetry, 5000)
        }
      }
    }

    fetchWithRetry()

    return () => {
      cancelled = true
      clearRetry()
    }
  }, [filters?.tag, filters?.stack, filters?.q])

  return { apps, loading }
}
