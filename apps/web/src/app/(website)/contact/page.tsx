import type { Metadata } from "next";
import { PageHero, Sec } from "@/components/website/sections/page-kit";
import own from "@/styles/simple-pages.module.css";

export const metadata: Metadata = {
  title: "Contact Us — Growixa",
  description: "There's no sales team. You'll get one of the founders directly.",
};

const ROUTES_TO: Array<[string, string, string, string]> = [
  [
    "find",
    "Something's broken",
    "Deliverability trouble, a campaign misbehaving, or anything urgent with sending.",
    "support@growixa.com",
  ],
  [
    "create",
    "Thinking about switching",
    "Migration questions, whether we fit, or a walkthrough with someone who built it.",
    "hello@growixa.com",
  ],
  [
    "manage",
    "Security or privacy",
    "DPA requests, vulnerability reports, data removal, procurement questionnaires.",
    "security@growixa.com",
  ],
];

export default function ContactPage() {
  return (
    <>
      <PageHero
        hue="find"
        title="There's no sales team. You'll get one of us."
        lede="Small company, so the addresses below go to actual people. Weekday replies within a business day, usually much sooner."
      />
      <Sec hue="find">
        <div className={own.cards}>
          {ROUTES_TO.map(([hue, title, body, addr]) => (
            <div
              key={addr}
              className={own.card}
              style={
                {
                  "--hue": `var(--${hue})`,
                  "--hue-l": `var(--${hue}-l)`,
                  "--hue-d": `var(--${hue}-d)`,
                } as React.CSSProperties
              }
            >
              <h3>{title}</h3>
              <p>{body}</p>
              <a href={`mailto:${addr}`} className={own.addr}>
                {addr}
              </a>
            </div>
          ))}
        </div>
        <p className={own.note}>
          Direct founder routing: support@growixa.com &middot; hello@growixa.com &middot;
          security@growixa.com
        </p>
      </Sec>
    </>
  );
}
