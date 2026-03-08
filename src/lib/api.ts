const BASE = "http://127.0.0.1:8742"
const TOKEN_KEY = "appdrop_token"

export type AppStatus = "installing"|"ready"|"running"|"error"|"stopped"|"queued"|"updating"
export type Stack = "python"|"node"|"docker"|"conda"|"unknown"

export interface App {
  id: string; name: string; github_url: string; stack: Stack
  status: AppStatus; install_pct: number; install_stage: string
  install_label: string; port: number|null; error_message: string|null
  launch_command: string|null; last_message: string; installed_at: number|null
}

export interface RegistryApp {
  id: string; name: string; description: string; github_url: string
  stack: Stack; tags: string[]; stars_approx: number; default_port: number
  verified: boolean; thumbnail: string; installed: boolean; installed_id?: string
  compatibility?: string
}

function getAuthHeader(): Record<string, string> {
  const token = localStorage.getItem(TOKEN_KEY)
  return token ? { Authorization: `Bearer ${token}` } : {}
}

async function req(path: string, opts?: RequestInit) {
  const r = await fetch(BASE + path, {
    headers: { "Content-Type": "application/json", ...getAuthHeader() },
    ...opts
  })
  if (!r.ok) throw new Error(`${r.status}: ${await r.text()}`)
  return r.json()
}

export const api = {
  health:        ()           => req("/health"),
  listApps:      ()           => req("/apps").then(d => d.apps as App[]),
  getApp:        (id:string)  => req(`/apps/${id}`) as Promise<App>,
  validateUrl:   (url:string) => req("/validate-url", {method:"POST", body: JSON.stringify({url})}),
  installApp:    (github_url:string, name?:string) =>
    req("/apps/install", {method:"POST", body: JSON.stringify({github_url, name})}),
  launchApp:     (id:string)  => req(`/apps/${id}/launch`, {method:"POST"}),
  stopApp:       (id:string)  => req(`/apps/${id}/stop`,   {method:"POST"}),
  deleteApp:     (id:string)  => req(`/apps/${id}`,        {method:"DELETE"}),
  updateApp:     (id:string)  => req(`/apps/${id}/update`, {method:"POST"}),
  updateCheck:   (id:string)  => req(`/apps/${id}/update-check`),
  getLogs:       (id:string)  => req(`/apps/${id}/logs`),
  systemInfo:    ()           => req("/system/info"),
  registry:      (params?:{tag?:string,stack?:string,q?:string}) => {
    const qs = params ? "?"+new URLSearchParams(Object.fromEntries(
      Object.entries(params).filter(([,v])=>v))) : ""
    return req("/registry"+qs).then(d => d.apps as RegistryApp[])
  },
  registryApp:   (id:string)  => req(`/registry/${id}`) as Promise<RegistryApp>,
  submitApp:     (data:object)=> req("/registry/submit", {method:"POST", body:JSON.stringify(data)}),
  authMe:        ()           => req("/auth/me"),
  authLogout:    ()           => req("/auth/logout", {method:"POST"}),
}
