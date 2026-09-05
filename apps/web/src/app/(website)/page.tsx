import type { Metadata } from "next";
import { ClassicHome } from "@/components/website/sections/classic-home";

export const metadata: Metadata = {
  title: "Growixa — AI Growth Execution Platform",
  description:
    "Plan, create, approve, execute and improve email and social campaigns from one intelligent growth workspace.",
};

export default function HomePage() {
  return <ClassicHome />;
}
