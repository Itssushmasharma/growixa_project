import type { Metadata } from "next";
import { PageHero, Sec, Head, Bento, ClosingCta } from "@/components/website/sections/page-kit";
import own from "@/styles/simple-pages.module.css";

export const metadata: Metadata = {
  title: "About Us & Founder Note — Growixa",
  description:
    "We're building the team we couldn't afford to hire. Four things we've decided not to negotiate.",
};

const BENTO_ITEMS = [
  {
    span: "w6" as const,
    title: "Say what is built, not what is planned",
    body: "Every feature carries a real status. Nothing on this site describes something that does not exist without saying so in the same breath.",
  },
  {
    span: "w6" as const,
    title: "No invented proof",
    body: "No fake testimonials, no stock-photo customers, no metric we cannot source.",
  },
  {
    span: "w6" as const,
    title: "Your data leaves when you do",
    body: "One-click full export, any time, including after cancellation.",
  },
  {
    span: "w6" as const,
    title: "Deliverability over volume",
    body: "We will keep building things that stop you sending — verification, suppression, warm-up ceilings — even though they lower the number on our invoice.",
  },
];

export default function AboutPage() {
  return (
    <>
      <PageHero
        hue="qualify"
        title="We're building the team we couldn't afford to hire."
        lede="Growixa started because we shipped a product, had no idea how to sell it, and found that every tool for doing so assumed we had already solved that."
      />
      <Sec hue="qualify">
        <div className={own.note2}>
          <div className={own.by}>
            <span className={own.avatar} aria-hidden="true">
              G
            </span>
            <div>
              <b>A note from the founders</b>
              <span>Written August 2026 · updated when it stops being true</span>
            </div>
          </div>
          <div className={own.prose}>
            <p>
              We spent four months building something we were proud of and then discovered the hard
              part had not started. Selling it meant a lead tool, a verifier, an enrichment service,
              a sequencer, a warm-up service, a copy tool and a CRM — around{" "}
              <strong>$220 a month and seven logins</strong> — before a single email went out. Every
              one of them was built for a team that already knew what it was doing.
            </p>
            <p>
              So we built the thing we wanted: one system that runs the whole motion, for people who
              do not have a go-to-market team and cannot yet justify hiring one.
            </p>
            <h3>Where we actually are</h3>
            <p>
              Two of the five stages are live and good — <strong>Send</strong> and{" "}
              <strong>Manage</strong>. Two are in beta and improving weekly. One,{" "}
              <strong>Qualify</strong>, does not exist yet and will not until Q4. We have written
              that on the pricing page, the roadmap and every product page, because finding out
              after you have paid is how companies lose people permanently.
            </p>
            <p>
              We have no customer logos on this site. We could have invented some — plenty do — but
              you are a founder and you would have checked. When we have customers willing to be
              named, they will be here with their real numbers.
            </p>
          </div>
        </div>
      </Sec>
      <Sec tint hue="qualify">
        <Head
          eyebrow="What we hold to"
          title="Four things we've decided not to negotiate."
          lede="Written down so you can hold us to them, and so we cannot quietly drift."
        />
        <Bento items={BENTO_ITEMS} />
      </Sec>
      <ClosingCta
        title="Fifty design partners."
        body="Direct line to the founders, roadmap influence, and pricing locked for as long as you stay."
        primary={{ to: "/contact", label: "Apply to join" }}
        secondary={{ to: "/roadmap", label: "See what's shipping" }}
      />
    </>
  );
}
