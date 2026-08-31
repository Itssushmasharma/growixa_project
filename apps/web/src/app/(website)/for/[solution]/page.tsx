import type { Metadata } from "next";
import { notFound } from "next/navigation";
import Link from "next/link";
import { SOLUTIONS } from "@/content/website/nav";
import {
  PageHero,
  Sec,
  Head,
  Bento,
  ClosingCta,
  Button,
} from "@/components/website/sections/page-kit";
import own from "@/styles/simple-pages.module.css";

interface SolutionDetail {
  hue: string;
  eyebrow: string;
  title: string;
  lede: string;
  head: { eyebrow: string; title: string; lede: string };
  features: Array<{
    span: "w4" | "w6" | "w8" | "w12";
    title: string;
    body: string;
    chips?: string[];
  }>;
  notForUs?: Array<[string, string]>;
}

const SOLUTION_CONTENT: Record<string, SolutionDetail> = {
  founders: {
    hue: "send",
    eyebrow: "FOR FOUNDERS",
    title: "Right now, you are the go-to-market team.",
    lede: "You built something good. Nobody knows. And the advice is to hire a growth person you cannot afford, or wire together nine tools you do not have time to learn. Growixa is the third option.",
    head: {
      eyebrow: "Built for your situation",
      title: "Nothing here assumes you have a team.",
      lede: "Every default assumes you will be back in the code in twenty minutes and nothing should be waiting on you.",
    },
    features: [
      {
        span: "w6",
        title: "No seats, ever",
        body: "Bring your co-founder and your first hire. Free plans included.",
        chips: ["Unlimited seats"],
      },
      {
        span: "w6",
        title: "Approval is off by default",
        body: "There is nobody to approve it. Turn it on when there is.",
      },
      {
        span: "w4",
        title: "The deliverability trap, avoided",
        body: "Warm-up and authentication run automatically. The mistake that kills a founder’s domain is the one you never see coming.",
      },
      {
        span: "w4",
        title: "Support is a founder",
        body: "On Growth you are talking to someone who wrote the thing, not a tier-one queue.",
      },
      {
        span: "w4",
        title: "Set up in an afternoon",
        body: "Connect a domain, import whatever you have, describe your customer, read the drafts. About forty minutes.",
      },
    ],
  },
  "gtm-teams": {
    hue: "find",
    eyebrow: "FOR GTM TEAMS",
    title: "Replace the stack you inherited.",
    lede: "You did not choose these nine tools. They accumulated. Now half your week is spent keeping data moving between them, and the integration nobody owns breaks on a Tuesday.",
    head: {
      eyebrow: "What changes",
      title: "Consolidation you can defend in a budget review.",
      lede: "The pitch to your CFO is cost. The pitch to your team is that the data stops disagreeing with itself.",
    },
    features: [
      {
        span: "w6",
        title: "One number instead of nine invoices",
        body: "Most teams cannot say what their GTM stack costs without opening a spreadsheet. One contract, one renewal date, one vendor review.",
        chips: ["One contract", "One renewal"],
      },
      {
        span: "w6",
        title: "Suppression that cannot be bypassed",
        body: "When unsubscribes live in one tool and sending lives in another, someone eventually emails a person who opted out. Here there is no second list to fall out of sync with.",
        chips: ["Global suppression", "Audit trail"],
      },
      {
        span: "w4",
        title: "Migration in an afternoon",
        body: "Lists, templates, sending history and suppression from Mailchimp, Klaviyo, Brevo or HubSpot.",
      },
      {
        span: "w4",
        title: "Keep your sending infrastructure",
        body: "Already invested in Postmark, SES or Sendgrid? Growixa runs the campaigns, they carry the mail.",
      },
      {
        span: "w4",
        title: "No hostage data",
        body: "Full export any time, including after you cancel. We would rather earn the renewal.",
      },
    ],
    notForUs: [
      [
        "You need enterprise ABM attribution today",
        "Multi-touch attribution across paid, events and web is not on our roadmap. Factors or Dreamdata will serve you better.",
      ],
      [
        "Your GTM runs on a data warehouse",
        "If your source of truth is Snowflake and you need reverse ETL, that is Hightouch’s job, not ours.",
      ],
      [
        "You have twelve SDRs and a sales engineering function",
        "At that size you want depth per tool, not consolidation. Apollo and Outreach are built for you.",
      ],
    ],
  },
  "marketing-teams": {
    hue: "create",
    eyebrow: "FOR MARKETING TEAMS",
    title: "AI copy you'd actually put your brand behind.",
    lede: "The reason marketing teams distrust AI writing is not quality — it is risk. One confident false claim in front of a customer costs more than the tool saved. Growixa makes the guardrails part of generation, not part of review.",
    head: {
      eyebrow: "The real objection",
      title: '"We tried AI copy. We spent longer editing it than writing it."',
      lede: "Usually true — because most tools generate first and personalise afterwards. The output is grammatical and completely generic, so a human rewrites it anyway.",
    },
    features: [
      {
        span: "w8",
        title: "Claims you have banned, it cannot make",
        body: "List what you are not allowed to say — a certification you do not hold, a superlative legal vetoed — and it is blocked at generation, not caught in review.",
        chips: ["Banned claims", "Required disclaimers", "Tone lock"],
      },
      {
        span: "w4",
        title: "You will still edit",
        body: "Anyone promising copy you send untouched is selling you something. The goal is an eighty-percent draft grounded in real facts.",
      },
      {
        span: "w4",
        title: "Approval before anything goes out",
        body: "An optional queue where a named person signs off on first-touch messages. Every decision logged against the contact.",
      },
      {
        span: "w4",
        title: "Templates that survive Outlook",
        body: "Drag-and-drop when you want design, plain text when you want replies. Both tested where it matters.",
      },
      {
        span: "w4",
        title: "Compliance you do not have to remember",
        body: "One-click unsubscribe, consent provenance, and a global suppression list every campaign checks first.",
      },
    ],
  },
};

interface SolutionPageProps {
  params: Promise<{ solution: string }>;
}

export async function generateStaticParams() {
  return SOLUTIONS.map((s) => ({ solution: s.id }));
}

export async function generateMetadata({ params }: SolutionPageProps): Promise<Metadata> {
  const { solution } = await params;
  const c = SOLUTION_CONTENT[solution];
  if (!c) return { title: "Solution Not Found — Growixa" };
  return {
    title: `${c.eyebrow} — Growixa`,
    description: c.lede,
  };
}

export default async function SolutionPage({ params }: SolutionPageProps) {
  const { solution } = await params;
  const c = SOLUTION_CONTENT[solution];

  if (!c) {
    notFound();
  }

  return (
    <>
      <PageHero
        hue={c.hue}
        eyebrow={c.eyebrow}
        title={c.title}
        lede={c.lede}
        actions={
          <>
            <Button as={Link} href="/register">
              Start free
            </Button>
            <Button as={Link} href="/platform" variant="glass">
              See the engine
            </Button>
          </>
        }
        foot="Free up to 1,000 contacts · No card · Set up in an afternoon"
      />

      <Sec hue={c.hue}>
        <Head {...c.head} />
        <Bento items={c.features} />
      </Sec>

      {c.notForUs && (
        <Sec tint hue={c.hue}>
          <Head
            center
            eyebrow="Straight answer"
            title="Where we're not the right choice."
            lede="Being honest about this saves us both a procurement cycle."
          />
          <div className={own.post}>
            {c.notForUs.map(([t, b]) => (
              <div key={t} className={own.postRow}>
                <span className={own.no}>Not us</span>
                <span className={own.pt}>
                  <b>{t}</b>
                  <span>{b}</span>
                </span>
              </div>
            ))}
            <div className={own.postRow}>
              <span className={own.yes}>Good fit</span>
              <span className={own.pt}>
                <b>A team of one to ten carrying the whole motion</b>
                <span>
                  Where the cost of switching between tools is a real fraction of the week.
                </span>
              </span>
            </div>
          </div>
        </Sec>
      )}

      <ClosingCta
        title="You built the product. Let Growixa build the pipeline."
        body="Free up to 1,000 contacts. If it does not save you a Tuesday, do not pay us."
        primary={{ to: "/register", label: "Start free" }}
        secondary={{ to: "/about", label: "Read why we built it" }}
      />
    </>
  );
}
