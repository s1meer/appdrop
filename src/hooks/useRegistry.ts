import { useState, useEffect } from "react"
import { api, RegistryApp } from "../lib/api"

export function useRegistry(filters?: {tag?:string,stack?:string,q?:string}) {
  const [apps, setApps] = useState<RegistryApp[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    setLoading(true)
    api.registry(filters).then(setApps).finally(() => setLoading(false))
  }, [filters?.tag, filters?.stack, filters?.q])

  return { apps, loading }
}
