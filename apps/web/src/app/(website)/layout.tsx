import type { Metadata } from "next";
import type { ReactNode } from "react";
import Header from "@/components/website/shell/header";
import Footer from "@/components/website/shell/footer";
import "@/styles/website-base.css";

export const metadata: Metadata = {
  metadataBase: new URL(process.env.NEXT_PUBLIC_APP_URL || "https://growixa.com"),
  title: {
    default: "Growixa — AI-powered Growth & Marketing Automation Platform",
    template: "%s | Growixa",
  },
  description:
    "Growixa is the AI-powered Growth & Marketing Automation Platform for agencies and scaling businesses. Unified inbox, analytics, social scheduling, and email campaigns in one intelligent workspace.",
  keywords: [
    "AI marketing platform",
    "email campaign software",
    "marketing automation",
    "campaign management",
    "AI content assistant",
  ],
  openGraph: {
    title: "Growixa — AI-powered Growth & Marketing Automation Platform",
    description: "Growixa is the AI-powered Growth & Marketing Automation Platform for agencies and scaling businesses. Unified inbox, analytics, social scheduling, and email campaigns in one intelligent workspace.",
    url: "https://growixa.com",
    siteName: "Growixa",
    images: [
      {
        url: "https://growixa.com/og-image.jpg",
        width: 1200,
        height: 630,
        alt: "Growixa Dashboard Preview",
      }
    ],
    type: "website",
    locale: "en_US",
  },
  twitter: {
    card: "summary_large_image",
    title: "Growixa — The Ultimate Agency Growth Engine",
    description: "Automate social, emails, and reporting. The only platform an agency needs.",
    images: ["https://growixa.com/twitter-image.jpg"],
    creator: "@growixa",
  },
  robots: { index: true, follow: true },
};

export default function WebsiteLayout({ children }: { children: ReactNode }) {
  const jsonLd = {
    "@context": "https://schema.org",
    "@type": "SoftwareApplication",
    "name": "Growixa",
    "applicationCategory": "BusinessApplication",
    "operatingSystem": "Web",
    "offers": {
      "@type": "Offer",
      "price": "0",
      "priceCurrency": "USD"
    },
    "description": "AI-powered Growth & Marketing Automation Platform."
  };

  return (
    <div className="website-root">
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{ __html: JSON.stringify(jsonLd) }}
      />
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
