import type { Metadata } from 'next';
import { Inter } from 'next/font/google';
import './globals.css';
import { AppProvider } from '@/contexts/AppContext';

const inter = Inter({ subsets: ['latin'] });

export const metadata: Metadata = {
  title: 'Prospecta IA',
  description: 'Sistema inteligente de prospeccao B2B',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="pt-BR">
      <body className={inter.className}>
        <AppProvider>
          <main className="min-h-screen bg-surface">
            {children}
          </main>
        </AppProvider>
      </body>
    </html>
  );
}
