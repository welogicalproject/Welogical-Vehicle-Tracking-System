import type { Metadata } from "next";
import "./globals.css";
import { Sidebar } from "../components/sidebar";
import { Header } from "../components/header";

export const metadata: Metadata = {
  title: "Vehicle Tracking System (VTS) Dashboard",
  description: "Real-time fleet tracking, packet debugging, and database explorer panel.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className="bg-[#0b0f19] text-white antialiased flex overflow-hidden">
        {/* Sidebar Nav */}
        <Sidebar />
        
        {/* Main Content Area */}
        <main className="flex-1 h-screen flex flex-col overflow-hidden bg-[#0b0f19]">
          <Header />
          <div className="flex-1 overflow-y-auto">
            {children}
          </div>
        </main>
      </body>
    </html>
  );
}

