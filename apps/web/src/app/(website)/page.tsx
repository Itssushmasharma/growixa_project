import type { Metadata } from "next";
import { ClassicHome } from "@/components/website/sections/classic-home";
import { FAQS } from "@/components/website/sections/classic-home-data";

export const metadata: Metadata = {
  title: "Growixa — AI Growth Execution Platform",
  description:
    "Plan, create, approve, execute and improve email and social campaigns from one intelligent growth workspace.",
  alternates: {
    canonical: "/",
  },
  openGraph: {
    title: "Growixa — AI Growth Execution Platform",
    description:
      "Turn marketing goals into approved, measurable campaigns from one intelligent workspace.",
    type: "website",
  },
};

export default function HomePage() {
  const structuredData = {
    "@context": "https://schema.org",
    "@graph": [
      {
        "@type": "SoftwareApplication",
        name: "Growixa",
        applicationCategory: "BusinessApplication",
        operatingSystem: "Web",
        description:
          "An AI-powered workspace for planning, creating, approving, executing and improving marketing campaigns.",
        offers: {
          "@type": "Offer",
          price: "0",
          priceCurrency: "USD",
          category: "Free plan",
        },
      },
      {
        "@type": "FAQPage",
        mainEntity: FAQS.map(([question, answer]) => ({
          "@type": "Question",
          name: question,
          acceptedAnswer: {
            "@type": "Answer",
            text: answer,
          },
        })),
      },
    ],
  };

  return (
    <>
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{
          __html: JSON.stringify(structuredData).replace(/</g, "\\u003c"),
        }}
      />
      <ClassicHome />
    </>
  );
}
