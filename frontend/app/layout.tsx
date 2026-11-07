import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Seekora — Search Beyond the Obvious",
  description: "Source-grounded hybrid discovery with traceable citations",
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
