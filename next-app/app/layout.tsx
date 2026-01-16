import type { Metadata } from "next";
import { Geist } from "next/font/google";
import "./globals.css";

const geist = Geist({
  subsets: ["latin"],
  weight: "200"
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
      <body className={`${geist.className} antialiased p-0 m-0`}>
        <div className="w-screen h-screen flex flex-col items-center overflow-hidden">
          {children}
        </div>
      </body>
    </html>
  );
}
