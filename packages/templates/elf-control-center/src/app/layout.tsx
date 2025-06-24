import type { Metadata } from 'next'
import { Inter } from 'next/font/google'
import { Providers } from './providers'
import { Navigation } from '@/components/navigation'
// Theme CSS is included in globals.css
import '@/styles/globals.css'

const inter = Inter({ subsets: ['latin'] })

export const metadata: Metadata = {
  title: 'ElfAutomations.ai Control Center',
  description: 'Real-time monitoring and control of your autonomous AI ecosystem',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en" className="dark">
      <body className={inter.className}>
        <Providers>
          <div className="flex h-screen bg-background">
            <Navigation />
            <main className="flex-1 overflow-y-auto">
              {children}
            </main>
          </div>
        </Providers>
      </body>
    </html>
  )
}
