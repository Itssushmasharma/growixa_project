"use client";

import { useState } from "react";
import { PageHero, Sec, ClosingCta, Button } from "@/components/website/sections/page-kit";
import own from "@/styles/interactive.module.css";

const PEOPLE = [
  ["PR", "Priya Raghavan", "VP Marketing", "northwind.io", true],
  ["DO", "Daniel Okoye", "Head of Growth", "lumenlabs.com", true],
  ["JW", "James Whitfield", "Marketing Lead", "pinehurst.dev", false],
  ["MT", "Mei Tanaka", "Founder", "clearstep.app", true],
  ["AB", "Adaeze Balogun", "COO", "tiderise.co", true],
];

interface CopyVariant {
  sub: string;
  body: string;
  meta: string;
}

const COPY: Record<"email" | "linkedin" | "sms", CopyVariant> = {
  email: {
    sub: "Northwind's pricing page, and the thing under it",
    body: `Hi Priya — you've been back to our pricing page three times this week, so I'll skip the intro.

The bit teams at your stage usually ask about first is whether sequences stop when a colleague replies from a different thread. They do.

Worth ten minutes on Tuesday?`,
    meta: "94 words · 0 banned claims · reading level 6",
  },
  linkedin: {
    sub: "Post draft · for Priya to share or review",
    body: `Most GTM stacks for Series A teams are nine tools held together by someone who wishes they were writing code instead.

We replaced the whole run with one engine. The first 50 design partners are live today:`,
    meta: "212 chars · no hashtags by rule · voice matched",
  },
  sms: {
    sub: "SMS preview · one segment, GSM-7",
    body: `Hi Priya, your Growixa trial is ready. 1,000 contacts and 2k sends loaded: growixa.com/t/pr92 (Reply STOP to opt out)`,
    meta: "148 chars · 1 segment · opt-out included",
  },
};

export default function SandboxPage() {
  const [finding, setFinding] = useState(false);
  const [channel, setChannel] = useState<"email" | "linkedin" | "sms">("email");
  const [writing, setWriting] = useState(false);

  const activeCopy = COPY[channel];

  const run = (setter: (v: boolean) => void) => {
    setter(true);
    setTimeout(() => setter(false), 900);
  };

  return (
    <>
      <PageHero
        hue="create"
        title="Try the engine on prepared data."
        lede="No signup, no tracking, nothing saved. Pick a stage below and watch what the data and the copy look like when they land."
      />

      <Sec hue="create">
        <div className={own.two}>
          <div
            className={own.box}
            style={
              {
                "--hue": "var(--find)",
                "--hue-l": "var(--find-l)",
                "--hue-d": "var(--find-d)",
              } as React.CSSProperties
            }
          >
            <div className={own.boxHead}>
              <span className={own.mono}>01 — Find</span>
              <h3>Describe a market. Get verified rows.</h3>
              <p>Type a description. It extracts the criteria and runs an MX check.</p>
            </div>
            <div className={own.boxBody}>
              <label className={own.field}>
                <span>Market description</span>
                <input
                  defaultValue="Series A B2B SaaS in the UK, hiring marketing"
                  aria-label="Market description"
                />
              </label>
              <Button onClick={() => run(setFinding)} disabled={finding} className={own.full}>
                {finding ? "Searching sources…" : "Run search"}
              </Button>
              <div className={own.out}>
                {finding ? (
                  <p className={own.pending}>Querying registries and running SMTP checks…</p>
                ) : (
                  PEOPLE.map(([ini, name, role, co, ok]) => (
                    <div key={co as string} className={own.person}>
                      <span className={own.ini} aria-hidden="true">
                        {ini}
                      </span>
                      <span className={ok ? own.pt : own.ptDim}>
                        <b>{name}</b>
                        <span>
                          {role} · {co}
                        </span>
                      </span>
                      <span className={ok ? own.ok : own.dim}>{ok ? "MX ok" : "Not billed"}</span>
                    </div>
                  ))
                )}
              </div>
            </div>
            <div className={own.boxFoot}>
              <span>Sample data · the real thing runs on live sources</span>
              <span>4 verified · 1 rejected · 4 credits</span>
            </div>
          </div>

          <div
            className={own.box}
            style={
              {
                "--hue": "var(--create)",
                "--hue-l": "var(--create-l)",
                "--hue-d": "var(--create-d)",
              } as React.CSSProperties
            }
          >
            <div className={own.boxHead}>
              <span className={own.mono}>03 — Create</span>
              <h3>Watch it write for a channel.</h3>
              <p>Same idea, three genuinely different pieces of writing.</p>
            </div>
            <div className={own.boxBody}>
              <label className={own.field}>
                <span>Channel</span>
                <select
                  value={channel}
                  onChange={(e) => setChannel(e.target.value as "email" | "linkedin" | "sms")}
                >
                  <option value="email">Email</option>
                  <option value="linkedin">LinkedIn post</option>
                  <option value="sms">SMS</option>
                </select>
              </label>
              <Button onClick={() => run(setWriting)} disabled={writing} className={own.full}>
                {writing ? "Writing…" : "Write it"}
              </Button>
              <div className={own.out}>
                {writing ? (
                  <p className={own.pending}>Reading their site…</p>
                ) : (
                  <div className={own.mail}>
                    <p className={own.mailSub}>{activeCopy.sub}</p>
                    <p className={own.mailBody}>{activeCopy.body}</p>
                  </div>
                )}
              </div>
            </div>
            <div className={own.boxFoot}>
              <span>Sample output · shows the shape, not live generation</span>
              <span>{activeCopy.meta}</span>
            </div>
          </div>
        </div>

        <div className={own.honest}>
          <h3>What&rsquo;s real here and what isn&rsquo;t</h3>
          <p>
            These two demos run on prepared data so they work instantly and cost you nothing. The
            product they represent is real: Send and Manage are live today, Find and Create are in
            open beta. We&rsquo;d rather show you a fast honest mock-up than a slow live demo you
            abandon — and rather say so than let you assume.
          </p>
        </div>
      </Sec>

      <ClosingCta
        title="Liked it? The free plan does this for real."
        body="1,000 contacts, 2,000 emails a month, no card. The same engine, pointed at your own market."
        primary={{ to: "/register", label: "Start free" }}
        secondary={{ to: "/platform", label: "How it fits together" }}
      />
    </>
  );
}
