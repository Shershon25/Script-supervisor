import type { Metadata } from 'next';
import './globals.css';

export const metadata: Metadata = {
  title: 'Script Supervisor — AI Screenplay Engine',
  description: 'AI-powered screenplay understanding, persistent story world memory, and continuity tracking.',
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className="dark">
      <head>
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="anonymous" />
        <link
          href="https://fonts.googleapis.com/css2?family=Courier+Prime:ital,wght@0,400;0,700;1,400&family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap"
          rel="stylesheet"
        />
      </head>
      <body className="bg-app text-primary min-h-screen font-sans antialiased selection:bg-accent selection:text-white">
        {children}
      </body>
    </html>
  );
}
