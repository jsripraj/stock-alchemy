import type { Metadata } from "next";
import { Sansation } from "next/font/google";
import "./globals.css";
import Header from "@/app/components/layout/Header";

const sansation = Sansation({
  weight: "300",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "StockAlchemy",
  description: "Filter stocks using custom formulas",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {

  return (
    <html lang="en">
      <body className={`${sansation.className} antialiased p-0 m-0`}>
        <div className="w-screen h-screen flex flex-col items-center overflow-hidden">
          <Header />
          {children}
        </div>
      </body>
    </html>
  );
}
