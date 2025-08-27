// layout.tsx
import './globals.css'

export const metadata = {
  title: 'Overtakr',
  description: 'F1 Strategy Visualizer',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  )
}
