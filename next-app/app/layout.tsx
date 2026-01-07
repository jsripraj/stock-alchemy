import type { Metadata } from "next";
import { Sansation } from "next/font/google";
import Image from "next/image";
import "./globals.css";
import localFont from "next/font/local";

const asimovian = localFont({
  src: "./fonts/Asimovian-Regular.ttf",
});

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
          <div className="flex my-6 items-center">
            <Image
              src="/logo.png"
              alt="Logo"
              width={50}
              height={50}
              className="object-contain"
            />
            <h1 className={`${asimovian.className} text-4xl text-lime-500`}>
              StockAlchemy
            </h1>
          </div>
          {children}
        </div>
      </body>
    </html>
  );
}
