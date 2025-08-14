'use client';

import type { Metadata } from 'next';
import { Montserrat } from 'next/font/google';
import './globals.css';
import { cn } from '@/lib/utils';
import { Toaster } from 'sonner';
import ThemeProvider from '@/components/theme/Provider';
import I18nProvider from '@/components/I18nProvider';
import { ChatProvider } from '@/lib/context/ChatContext';
import { useEffect } from 'react';
import { registerServiceWorker } from '@/lib/registerSW';

const montserrat = Montserrat({
  weight: ['300', '400', '500', '700'],
  subsets: ['latin'],
  display: 'swap',
  fallback: ['Arial', 'sans-serif'],
});

const metadata: Metadata = {
  title: 'Novas - Professional deep research',
  description: 'Novas is an AI powered chatbot that is connected to the internet and can do deep research .',
  manifest: '/manifest.json',
  themeColor: '#000000',
  appleWebApp: {
    capable: true,
    statusBarStyle: 'default',
    title: 'Novas',
  },
  viewport: {
    width: 'device-width',
    initialScale: 1,
    maximumScale: 1,
    userScalable: false,
  },
  icons: {
    icon: [
      { url: '/favicon.ico' },
      { url: '/icons/icon-192x192.png', sizes: '192x192', type: 'image/png' },
      { url: '/icons/icon-512x512.png', sizes: '512x512', type: 'image/png' },
    ],
    apple: [
      { url: '/icons/apple-touch-icon.png' },
    ],
  },
  openGraph: {
    type: 'website',
    title: 'Novas - Professional deep research',
    description: 'Novas is an AI powered chatbot that is connected to the internet and can do deep research.',
    siteName: 'Novas',
  },
  twitter: {
    card: 'summary_large_image',
    title: 'Novas - Professional deep research',
    description: 'Novas is an AI powered chatbot that is connected to the internet and can do deep research.',
  },
};

function PWALifecycle() {
  useEffect(() => {
    registerServiceWorker();
  }, []);

  return null;
}

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html className="h-full" suppressHydrationWarning>
      <body className={cn('h-full', montserrat.className)}>
        <ChatProvider>
          <I18nProvider>
            <ThemeProvider>
              <PWALifecycle />
              <div>{children}</div>
              <Toaster
                toastOptions={{
                  unstyled: true,
                  classNames: {
                    toast:
                      'bg-light-primary dark:bg-dark-secondary dark:text-white/70 text-black-70 rounded-lg p-4 flex flex-row items-center space-x-2',
                  },
                }}
              />
            </ThemeProvider>
          </I18nProvider>
        </ChatProvider>
      </body>
    </html>
  );
} 