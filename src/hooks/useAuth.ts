import { useState, useCallback } from "react"

const TOKEN_KEY = "appdrop_token"
const BASE = "http://127.0.0.1:8742"

export interface AuthUser {
  id: string
  email: string
  name: string
  avatar_url?: string
  provider: string
  isGuest?: boolean
}

function getToken(): string | null {
  return localStorage.getItem(TOKEN_KEY)
}

function setToken(token: string) {
  localStorage.setItem(TOKEN_KEY, token)
}

function clearToken() {
  localStorage.removeItem(TOKEN_KEY)
}

function decodeJwtPayload(token: string): Record<string, unknown> | null {
  try {
    const parts = token.split(".")
    if (parts.length < 2) return null
    const pad = (s: string) => s + "=".repeat((4 - s.length % 4) % 4)
    return JSON.parse(atob(pad(parts[1])))
  } catch {
    return null
  }
}

function tokenToUser(token: string): AuthUser | null {
  const payload = decodeJwtPayload(token)
  if (!payload) return null
  // Guest pseudo-token
  if (payload.guest) {
    return {
      id: payload.sub as string || "guest",
      email: "guest@local",
      name: "Guest",
      provider: "guest",
      isGuest: true,
    }
  }
  return {
    id: payload.sub as string || "",
    email: payload.email as string || "",
    name: payload.name as string || "",
    avatar_url: payload.avatar as string | undefined,
    provider: payload.provider as string || "unknown",
  }
}

function generateGuestToken(): string {
  const payload = {
    sub: "guest-" + Math.random().toString(36).slice(2),
    guest: true,
    iat: Math.floor(Date.now() / 1000),
    exp: Math.floor(Date.now() / 1000) + 30 * 24 * 3600,
  }
  const header = btoa('{"alg":"none","typ":"JWT"}').replace(/=/g,"")
  const body   = btoa(JSON.stringify(payload)).replace(/=/g,"")
  return `${header}.${body}.`
}

export function useAuth() {
  const stored = getToken()
  const [token, setTokenState] = useState<string | null>(stored)
  const user = token ? tokenToUser(token) : null

  const login = useCallback(async (provider: "google" | "github" | "guest") => {
    if (provider === "guest") {
      const t = generateGuestToken()
      setToken(t)
      setTokenState(t)
      return
    }

    return new Promise<void>((resolve, reject) => {
      const popup = window.open(
        `${BASE}/auth/${provider}`,
        "appdrop-auth",
        "width=500,height=650,left=200,top=100"
      )
      if (!popup) { reject(new Error("Popup blocked")); return }

      // Listen for redirect with ?token= in the popup URL
      const interval = setInterval(() => {
        try {
          const popupUrl = popup.location.href
          if (popupUrl.includes("token=")) {
            const params = new URLSearchParams(popupUrl.split("?")[1] || "")
            const t = params.get("token")
            if (t) {
              setToken(t)
              setTokenState(t)
              popup.close()
              clearInterval(interval)
              resolve()
            }
          }
        } catch {
          // Cross-origin — still waiting
        }
        if (popup.closed) {
          clearInterval(interval)
          resolve()
        }
      }, 300)

      // Also listen for postMessage
      const handler = (e: MessageEvent) => {
        if (e.data?.token) {
          setToken(e.data.token)
          setTokenState(e.data.token)
          popup.close()
          clearInterval(interval)
          window.removeEventListener("message", handler)
          resolve()
        }
      }
      window.addEventListener("message", handler)
    })
  }, [])

  const logout = useCallback(() => {
    clearToken()
    setTokenState(null)
  }, [])

  return {
    user,
    token,
    isLoggedIn: !!user,
    login,
    logout,
    getToken,
  }
}
