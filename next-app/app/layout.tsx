import type { Metadata } from "next";
import { Sansation } from "next/font/google";
import "./globals.css";

const sansation = Sansation({
  weight: "300",
  subsets: ["latin"],
})

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
      <body
        className={`${sansation.className} antialiased p-0 m-0`}
      >
        {children}
      </body>
    </html>
  );
}
