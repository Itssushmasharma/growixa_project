import type { Metadata } from "next";
import type { ReactNode } from "react";

export const metadata: Metadata = {
  title: "Pricing — Simple Plans for Growing Marketing Teams",
  description:
    "Compare Growixa plans for contacts, email campaigns, AI content and team approvals. Start free and upgrade when your marketing grows.",
  alternates: { canonical: "/pricing" },
  openGraph: {
    title: "Growixa Pricing — Start Free",
    description: "Simple marketing plans with clear contact, email and AI usage limits.",
  },
};

export default function PricingLayout({ children }: { children: ReactNode }) {
  return children;
}
