import type { Metadata } from 'next'
import { Inter, Manrope } from 'next/font/google'
import './globals.css'

const inter = Inter({ 
  subsets: ['latin'],
  variable: '--font-inter',
})

const manrope = Manrope({ 
  subsets: ['latin'],
  variable: '--font-manrope',
})

export const metadata: Metadata = {
  title: 'takeabreak.life - Intelligent Wellness for Busy Professionals',
  description: 'Transform your workday with AI-powered break recommendations that prevent burnout and boost productivity.',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en" className={`${inter.variable} ${manrope.variable}`}>
      <body className="font-sans antialiased">{children}</body>
    </html>
  )
}