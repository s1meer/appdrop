export const metadata = { title: 'AppDrop', description: 'Turn any GitHub repo into a running app' }
export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body style={{margin:0,padding:0,background:"#0A0C11",fontFamily:"system-ui,sans-serif"}}>
        {children}
      </body>
    </html>
  )
}
