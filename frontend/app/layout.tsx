import "./globals.css";
import { Inter } from "next/font/google";
import { SiteHeader } from "@/components/site-header";

const inter = Inter({ subsets: ["latin"], variable: "--font-inter" });

export const metadata = {
  title: "CoursePulse AI",
  description: "Turn sleepy lecture slides into a personal TA report",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className={inter.variable}>
      <body className="min-h-screen bg-white text-gray-900 font-sans antialiased">
        <SiteHeader />
        {children}
      </body>
    </html>
  );
}
