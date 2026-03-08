// AppDrop - self-contained App.tsx (no missing component imports)
export default function App() {
  return (
    <div style={{ background: "#0A0C11", minHeight: "100vh", color: "#E8EAF0",
      fontFamily: "system-ui, sans-serif", display: "flex", alignItems: "center", justifyContent: "center" }}>
      <div style={{ textAlign: "center" }}>
        <div style={{ fontSize: 48, marginBottom: 16 }}>▼</div>
        <h1 style={{ fontSize: 32, fontWeight: 800, marginBottom: 8 }}>AppDrop</h1>
        <p style={{ color: "#5A6278" }}>Turn any GitHub repo into a running app — no terminal, no code.</p>
      </div>
    </div>
  )
}
