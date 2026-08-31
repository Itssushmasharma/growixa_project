import type { ReactNode } from "react";
import Header from "@/components/website/shell/header";
import Footer from "@/components/website/shell/footer";
import "@/styles/website-base.css";

export default function WebsiteLayout({ children }: { children: ReactNode }) {
  return (
    <div className="website-root">
      <a className="website-skip-link" href="#main">
        Skip to content
      </a>
      <Header />
      <main id="main" tabIndex={-1} style={{ flex: 1 }}>
        {children}
      </main>
      <Footer />
    </div>
  );
}
