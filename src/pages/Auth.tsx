import { useState } from "react"
import { useAuth } from "../hooks/useAuth"

interface Props {
  theme: "dark" | "light"
  onAuth: () => void
}

export default function Auth({ theme, onAuth }: Props) {
  const { login } = useAuth()
  const [loading, setLoading] = useState<string | null>(null)

  const bg     = theme === "dark" ? "#0A0C11" : "#F4F6FF"
  const card   = theme === "dark" ? "#0D0F15" : "#FFFFFF"
  const text   = theme === "dark" ? "#E8EAF0" : "#1A1D2E"
  const sub    = theme === "dark" ? "#5A6278" : "#8A8FA8"
  const border = theme === "dark" ? "#1A1D2E" : "#D8DCF0"

  async function handleLogin(provider: "google" | "github" | "guest") {
    setLoading(provider)
    try {
      await login(provider)
      onAuth()
    } catch {
      setLoading(null)
    }
  }

  return (
    <div style={{
      display: "flex", alignItems: "center", justifyContent: "center",
      width: "100vw", height: "100vh", background: bg,
      fontFamily: "-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif"
    }}>
      <div style={{
        background: card, border: `1px solid ${border}`, borderRadius: 16,
        padding: "40px 36px", width: 340, textAlign: "center",
        boxShadow: theme === "dark" ? "0 24px 64px rgba(0,0,0,0.5)" : "0 8px 32px rgba(0,0,0,0.12)"
      }}>
        {/* Logo */}
        <div style={{ marginBottom: 8 }}>
          <img src="/icons/icon.png" width={48} height={48} style={{ borderRadius: 10 }} />
        </div>
        <div style={{ fontSize: 24, fontWeight: 900, color: text, letterSpacing: -0.5, marginBottom: 4 }}>
          AppDrop
        </div>
        <div style={{ fontSize: 13, color: sub, marginBottom: 32 }}>
          One-click local AI app launcher
        </div>

        {/* Google */}
        <button
          onClick={() => handleLogin("google")}
          disabled={!!loading}
          style={{
            width: "100%", padding: "11px 16px", borderRadius: 8, marginBottom: 10,
            border: `1px solid ${border}`, background: loading === "google" ? "#3367D6" : "#4285F4",
            color: "#fff", fontSize: 14, fontWeight: 600, cursor: loading ? "wait" : "pointer",
            display: "flex", alignItems: "center", justifyContent: "center", gap: 10,
            opacity: loading && loading !== "google" ? 0.5 : 1, transition: "all 0.15s"
          }}>
          <svg width="18" height="18" viewBox="0 0 48 48">
            <path fill="#fff" d="M44.5 20H24v8h11.8C34.6 33.1 30 36 24 36c-6.6 0-12-5.4-12-12s5.4-12 12-12c3 0 5.7 1.1 7.8 2.9l5.7-5.7C34 6.1 29.3 4 24 4 12.9 4 4 12.9 4 24s8.9 20 20 20 20-8.9 20-20c0-1.3-.1-2.7-.4-4z"/>
          </svg>
          {loading === "google" ? "Signing in…" : "Sign in with Google"}
        </button>

        {/* GitHub */}
        <button
          onClick={() => handleLogin("github")}
          disabled={!!loading}
          style={{
            width: "100%", padding: "11px 16px", borderRadius: 8, marginBottom: 24,
            border: `1px solid ${border}`,
            background: loading === "github" ? "#1a1d24" : (theme === "dark" ? "#21262D" : "#24292F"),
            color: "#fff", fontSize: 14, fontWeight: 600, cursor: loading ? "wait" : "pointer",
            display: "flex", alignItems: "center", justifyContent: "center", gap: 10,
            opacity: loading && loading !== "github" ? 0.5 : 1, transition: "all 0.15s"
          }}>
          <svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor">
            <path d="M12 0C5.37 0 0 5.37 0 12c0 5.3 3.44 9.8 8.2 11.4.6.1.82-.26.82-.58v-2.2c-3.34.72-4.04-1.42-4.04-1.42-.54-1.38-1.33-1.74-1.33-1.74-1.09-.74.08-.73.08-.73 1.2.08 1.84 1.24 1.84 1.24 1.07 1.83 2.8 1.3 3.49 1 .1-.78.42-1.3.76-1.6-2.67-.3-5.47-1.33-5.47-5.93 0-1.31.47-2.38 1.24-3.22-.14-.3-.54-1.52.1-3.18 0 0 1-.32 3.3 1.23a11.5 11.5 0 0 1 6 0c2.28-1.55 3.28-1.23 3.28-1.23.65 1.66.24 2.88.12 3.18.77.84 1.24 1.91 1.24 3.22 0 4.61-2.8 5.63-5.48 5.92.42.36.81 1.1.81 2.22v3.29c0 .32.22.7.83.58C20.57 21.8 24 17.3 24 12c0-6.63-5.37-12-12-12z"/>
          </svg>
          {loading === "github" ? "Signing in…" : "Sign in with GitHub"}
        </button>

        {/* Skip */}
        <button
          onClick={() => handleLogin("guest")}
          disabled={!!loading}
          style={{
            background: "none", border: "none", color: sub, fontSize: 13,
            cursor: "pointer", textDecoration: "underline", padding: 0,
            opacity: loading && loading !== "guest" ? 0.4 : 1
          }}>
          Continue without account →
        </button>
      </div>
    </div>
  )
}
