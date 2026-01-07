"use client";

import Image from "next/image";
import Link from 'next/link';
import localFont from "next/font/local";

const asimovian = localFont({
  src: "../../fonts/Asimovian-Regular.ttf",
});

export default function Header() {
  return (
    <div className="flex my-6 items-center">
      <Link href="/">
        <Image
          src="/logo.png"
          alt="Logo"
          width={50}
          height={50}
          className="object-contain"
        />
      </Link>
      <Link href="/">
        <h1 className={`${asimovian.className} text-4xl text-lime-500`}>
          StockAlchemy
        </h1>
      </Link>
    </div>
  );
}