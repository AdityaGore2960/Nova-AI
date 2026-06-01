import type { Metadata } from 'next';
import { Inter } from 'next/font/google';
import './globals.css';
import Sidebar from '@/components/layout/Sidebar';

const inter = Inter({ subsets: ['latin'] });

export const metadata: Metadata = {
  title: 'Nova-AI - Multimodal Intelligence',
  description: 'Production-grade Nova-AI platform for intelligent workflows',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className="dark">
      <body className={`${inter.className} h-screen flex overflow-hidden bg-[var(--color-background)] text-white`}>
        <Sidebar />
        <main className="flex-1 flex flex-col min-w-0 h-full relative">
          {children}
        </main>
      </body>
    </html>
  );
}
