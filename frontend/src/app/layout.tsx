import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";

const inter = Inter({ subsets: ["latin"] });

export const metadata: Metadata = {
  title: "Aurora",
  description:
    "Aurora is an AI ecosystem that empowers young professionals from onboarding to leadership by providing personalized guidance, skills growth planning, and transparent feedback. Our mission: align with SAP’s motto 'help the world run better and improve people’s lives' while showcasing Responsible AI and business scalability.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className="h-full">
      <body className={`${inter.className} min-h-screen antialiased`}>
        {children}
      </body>
    </html>
  );
}
