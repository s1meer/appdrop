import { Toast, ToastType } from "../hooks/useToast"

const COLORS: Record<ToastType, string> = {
  success: "#2ECC71", error: "#E74C3C", warning: "#F39C12", info: "#4F8EF7"
}
const ICONS: Record<ToastType, string> = {
  success: "✓", error: "✕", warning: "⚠", info: "ℹ"
}

interface Props { toasts: Toast[]; onRemove: (id: string) => void }

export default function ToastContainer({ toasts, onRemove }: Props) {
  if (toasts.length === 0) return null
  return (
    <div style={{
      position: "fixed", top: 20, right: 20, zIndex: 9999,
      display: "flex", flexDirection: "column", gap: 8, maxWidth: 320, pointerEvents: "none"
    }}>
      {toasts.map(t => (
        <div key={t.id} style={{
          background: "#1A1D2E", border: `1px solid ${COLORS[t.type]}40`,
          borderLeft: `3px solid ${COLORS[t.type]}`,
          borderRadius: 8, padding: "11px 14px",
          display: "flex", alignItems: "center", gap: 10,
          boxShadow: "0 4px 20px rgba(0,0,0,0.4)",
          pointerEvents: "all",
          animation: "toastIn 0.2s ease"
        }}>
          <span style={{ color: COLORS[t.type], fontSize: 14, fontWeight: 700, flexShrink: 0 }}>
            {ICONS[t.type]}
          </span>
          <span style={{ color: "#E8EAF0", fontSize: 13, flex: 1, lineHeight: 1.4 }}>{t.message}</span>
          <button onClick={() => onRemove(t.id)} style={{
            background: "none", border: "none", color: "#5A6278",
            cursor: "pointer", fontSize: 14, padding: 0, flexShrink: 0
          }}>✕</button>
        </div>
      ))}
      <style>{`@keyframes toastIn{from{opacity:0;transform:translateX(24px)}to{opacity:1;transform:translateX(0)}}`}</style>
    </div>
  )
}
