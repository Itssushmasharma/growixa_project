import type { Metadata } from "next";
import Hero from "@/components/website/sections/hero";
import Marquee from "@/components/website/sections/marquee";
import Sprawl from "@/components/website/sections/sprawl";
import EngineBento from "@/components/website/sections/engine-bento";
import { AiSection, CtaBand } from "@/components/website/sections/ai-and-cta";

export const metadata: Metadata = {
  title: "Growixa — Your AI GTM Team Working While You Sleep",
  description:
    "The all-in-one go-to-market engine for companies without a GTM team. It finds your buyers, spots who is ready to talk, writes the outreach and runs the campaigns — replacing 25 tools.",
};

export default function HomePage() {
  return (
    <>
      {/* 1. State the wedge, and show the whole engine at once. */}
      <Hero />
      {/* 2. Make the sprawl visceral before explaining the alternative. */}
      <Marquee />
      <Sprawl />
      {/* 3. Explain the product, then prove the AI claims are checkable. */}
      <EngineBento />
      <AiSection />
      <CtaBand />
    </>
  );
}
