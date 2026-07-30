import type { Metadata } from "next";
import type { ReactNode } from "react";

import { ToastProvider } from "@/components/toast/toast-context";

import "./globals.css";

export const metadata: Metadata = {
  title: "Growixa",
  description: "Growixa dashboard",
};

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="en">
      <body>
        <ToastProvider>{children}</ToastProvider>
      </body>
    </html>
  );
}
