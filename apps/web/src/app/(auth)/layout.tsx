import type { ReactNode } from "react";
import "@/styles/website-base.css";

export default function AuthLayout({ children }: { children: ReactNode }) {
  return <div className="website-root">{children}</div>;
}
