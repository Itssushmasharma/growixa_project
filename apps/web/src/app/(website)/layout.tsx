import type { Metadata } from "next";
import type { ReactNode } from "react";
import Header from "@/components/website/shell/header";
import Footer from "@/components/website/shell/footer";
import "@/styles/website-base.css";

export const metadata: Metadata = {
  metadataBase: new URL(process.env.NEXT_PUBLIC_APP_URL || "https://growixa.com"),
  title: {
    default: "Growixa — AI Growth Execution Platform",
    template: "%s | Growixa",
  },
  description:
    "Plan, create, approve, execute and improve email and social campaigns from one intelligent marketing workspace.",
  keywords: [
    "AI marketing platform",
    "email campaign software",
    "marketing automation",
    "campaign management",
    "AI content assistant",
  ],
  openGraph: {
    siteName: "Growixa",
    type: "website",
    locale: "en_US",
  },
  robots: { index: true, follow: true },
};

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
