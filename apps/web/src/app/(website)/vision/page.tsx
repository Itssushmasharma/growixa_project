import type { Metadata } from "next";
import { PageHero, Sec, Head, Bento, ClosingCta } from "@/components/website/sections/page-kit";

export const metadata: Metadata = {
  title: "Our Vision & Mission — Growixa",
  description:
    "We envision a world where growth and marketing automation is accessible to companies of all sizes, without needing an entire go-to-market team.",
};

const BENTO_ITEMS = [
  {
    span: "w6" as const,
    title: "Democratizing Growth",
    body: "We believe that the best products should win, not just the products with the biggest marketing budgets. Growixa levels the playing field.",
  },
  {
    span: "w6" as const,
    title: "AI as a Co-Pilot, not a replacement",
    body: "Our AI doesn't just replace human effort; it amplifies it. You remain the strategist, and Growixa executes the play.",
  },
  {
    span: "w12" as const,
    title: "Unified workflows, zero silos",
    body: "No more stitching together 7 different tools for a single campaign. A unified workspace for social, email, analytics, and CRM.",
  }
];

export default function VisionPage() {
  return (
    <>
      <PageHero
        hue="create"
        title="Our Vision & Mission"
        lede="To build the ultimate go-to-market engine for companies that don't have a go-to-market team yet."
      />
      
      <Sec hue="create">
        <div style={{ maxWidth: "800px", margin: "0 auto", fontSize: "1.125rem", lineHeight: "1.8", color: "var(--mut)" }}>
          <p style={{ marginBottom: "1.5rem" }}>
            The current landscape of marketing software is fragmented and unnecessarily complex. 
            Founders and small teams spend more time managing their tools than they do engaging with their customers.
          </p>
          <p style={{ marginBottom: "1.5rem" }}>
            Our mission at Growixa is to eliminate this friction. We are building a platform that acts as your dedicated growth team—handling the heavy lifting of scheduling, sequencing, and analytics—so you can focus on building a great product.
          </p>
          <p>
            We&apos;re not just building another CRM or another email sender. We&apos;re building a unified engine powered by intelligent automation.
          </p>
        </div>
      </Sec>

      <Sec tint hue="create">
        <Head
          eyebrow="Core Principles"
          title="The foundation of everything we build."
          lede="These values guide every product decision, design choice, and customer interaction."
        />
        <Bento items={BENTO_ITEMS} />
      </Sec>

      <ClosingCta
        title="Join us on this journey."
        body="Experience the future of marketing automation today."
        primary={{ to: "/register", label: "Start your free trial" }}
        secondary={{ to: "/about", label: "Read our founder's note" }}
      />
    </>
  );
}
