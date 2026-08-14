import type { Metadata } from 'next'
import './globals.css'

export const metadata: Metadata = {
  title: 'NTPE Reader',
  description: 'NTPE Translation Reader Web App',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="zh-TW">
      <body>{children}</body>
    </html>
  )
}