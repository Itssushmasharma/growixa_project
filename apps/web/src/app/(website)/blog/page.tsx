import type { Metadata } from "next";
import { PageHero, Sec, Head } from "@/components/website/sections/page-kit";
import own from "@/styles/simple-pages.module.css";

export const metadata: Metadata = {
  title: "Blog & Articles — Growixa",
  description: "Upcoming engineering transparency and GTM growth insights from the team.",
};

const UPCOMING_POSTS: Array<[string, string]> = [
  ["Soon", "What we learned warming a cold domain, with the actual numbers"],
  ["Soon", "Why we shipped sending before lead sourcing"],
  ["Later", "The intent signals that turned out not to predict anything"],
  ["Later", "Building a GTM tool when you have never worked in GTM"],
];

export default function BlogPage() {
  return (
    <>
      <PageHero
        hue="create"
        title="Nothing here yet."
        lede="We'd rather have an empty blog than four posts written to fill a nav item. When we've learned something worth the read, it'll be here."
      />
      <Sec hue="create">
        <Head
          center
          title="What we're planning to write"
          lede="All of it from running this thing ourselves."
        />
        <div className={own.soonList}>
          {UPCOMING_POSTS.map(([when, title]) => (
            <div key={title} className={own.soonRow}>
              <span className={own.when}>{when}</span>
              <span>{title}</span>
            </div>
          ))}
        </div>
      </Sec>
    </>
  );
}
