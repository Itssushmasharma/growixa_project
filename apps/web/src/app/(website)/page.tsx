import type { Metadata } from "next";
import { PremiumGrowixaHome } from "@/components/website/sections/premium-home";
import { FAQS } from "@/components/website/sections/classic-home-data";

export const metadata: Metadata = {
  title: "Growixa — Social Media Management Tool",
  description:
    "Publish, analyze, and engage across all your social platforms from one intuitive dashboard.",
  alternates: {
    canonical: "/",
  },
  openGraph: {
    title: "Growixa — Social Media Management Tool",
    description:
      "Publish, analyze, and engage across all your social platforms from one intuitive dashboard.",
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
          "An intelligent workspace for social media publishing, analytics, and engagement.",
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
      <PremiumGrowixaHome />
    </>
  );
}
