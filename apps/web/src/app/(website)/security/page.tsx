import type { Metadata } from "next";
import { PageHero, Sec, Head, ClosingCta } from "@/components/website/sections/page-kit";
import own from "@/styles/simple-pages.module.css";

export const metadata: Metadata = {
  title: "Security & Posture — Growixa",
  description:
    "What we hold, where it lives, and what we don't have yet. Honest security posture and data provenance.",
};

const POSTURE: Array<["yes" | "soon" | "no", string, string]> = [
  [
    "yes",
    "Encryption in transit and at rest",
    "TLS 1.3 everywhere. AES-256 at rest, including database backups.",
  ],
  [
    "yes",
    "Tenant isolation",
    "Every row is scoped to an account at the database layer, enforced in queries rather than application logic.",
  ],
  [
    "yes",
    "Credential encryption",
    "SMTP and third-party credentials are encrypted with per-tenant keys and never logged or displayed after entry.",
  ],
  [
    "yes",
    "Least-privilege access",
    "A named subset of the team can reach production. Access is logged, reviewed monthly, revoked the day someone leaves.",
  ],
  [
    "soon",
    "SOC 2 Type II",
    "Observation window opens Q1 2027. We will not claim it, or imply it, before the report exists.",
  ],
  [
    "soon",
    "Third-party penetration test",
    "First external test scheduled for Q4 2026. Summary published here when it is done.",
  ],
  [
    "no",
    "ISO 27001",
    "Not started. If it is a procurement blocker for you, tell us — it moves up the list when customers need it.",
  ],
  [
    "no",
    "SSO & SCIM",
    "On the 2027 roadmap. Available on Scale before general release if you need it.",
  ],
  ["no", "HIPAA / FedRAMP", "Out of scope. Growixa is not suitable for protected health data."],
];

export default function SecurityPage() {
  return (
    <>
      <PageHero
        hue="manage"
        title="What we hold, where it lives, and what we don't have yet."
        lede="Most security pages are a wall of badges. We are a young company and we do not have all of them, so this page tells you exactly what is true today instead."
      />
      <Sec hue="manage">
        <Head center title="Our posture, honestly" />
        <div className={own.post}>
          {POSTURE.map(([state, t, b]) => (
            <div key={t} className={own.postRow}>
              <span className={own[state]}>
                {state === "yes" ? "In place" : state === "soon" ? "In progress" : "Not yet"}
              </span>
              <span className={own.pt}>
                <b>{t}</b>
                <span>{b}</span>
              </span>
            </div>
          ))}
        </div>
        <p className={own.note}>
          Lead data comes from public business sources only — company websites, public professional
          profiles, job boards, company registries and press releases. Every record carries its
          provenance. Removal requests are honoured within 30 days, from the individual directly.
        </p>
      </Sec>
      <ClosingCta
        title="Found something?"
        body="Email security@growixa.com. We acknowledge within one business day and we will not threaten you."
        primary={{ to: "/contact", label: "Contact us" }}
      />
    </>
  );
}
