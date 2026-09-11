import './globals.css';

export const metadata = {
  title: 'Ruler — Banking Regulatory AI Dashboard',
  description: 'Next.js & Tailwind CSS Banking Regulatory Intelligence Assistant with Per-Turn Token Telemetry.',
};

export default function RootLayout({ children }) {
  return (
    <html lang="en" className="dark">
      <head>
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="anonymous" />
        <link
          href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600&display=swap"
          rel="stylesheet"
        />
      </head>
      <body className="bg-[#FAF8F5] text-[#002147] font-sans min-h-screen flex flex-col antialiased">
        {children}
      </body>
    </html>
  );
}
