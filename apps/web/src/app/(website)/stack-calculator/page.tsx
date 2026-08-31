"use client";

import { useMemo, useState } from "react";
import { PageHero, Sec, ClosingCta } from "@/components/website/sections/page-kit";
import own from "@/styles/interactive.module.css";

type ToolTuple = [string, number, boolean?];
type StackSection = [string, string, ToolTuple[]];

const STACK: StackSection[] = [
  [
    "find",
    "Replaced by 01 — Find",
    [
      ["Apollo", 49, true],
      ["Hunter.io", 34],
      ["Clearbit", 99],
      ["ZoomInfo", 250],
      ["NeverBounce", 39],
    ],
  ],
  [
    "qualify",
    "Replaced by 02 — Qualify",
    [
      ["Clay", 149],
      ["Common Room", 99],
      ["RB2B / de-anon", 79],
    ],
  ],
  [
    "create",
    "Replaced by 03 — Create",
    [
      ["Jasper", 49, true],
      ["Copy.ai", 49],
      ["ChatGPT Plus", 20],
    ],
  ],
  [
    "send",
    "Replaced by 04 — Send",
    [
      ["Mailchimp", 60, true],
      ["Klaviyo", 70],
      ["Lemlist", 59, true],
      ["Instantly", 37],
      ["Smartlead", 39],
      ["Warmbox", 15, true],
    ],
  ],
  [
    "manage",
    "Replaced by 05 — Manage",
    [
      ["HubSpot Starter", 20, true],
      ["Zapier", 29, true],
      ["Airtable", 25],
    ],
  ],
];

const GROWIXA = 89;

export default function StackCalculatorPage() {
  const [picked, setPicked] = useState<Record<string, boolean>>(() => {
    const init: Record<string, boolean> = {};
    STACK.forEach(([, , tools]) => tools.forEach(([n, , on]) => on && (init[n] = true)));
    return init;
  });

  const { total, count } = useMemo(() => {
    let t = 0;
    let c = 0;
    STACK.forEach(([, , tools]) =>
      tools.forEach(([n, price]) => {
        if (picked[n]) {
          t += price;
          c += 1;
        }
      }),
    );
    return { total: t, count: c };
  }, [picked]);

  const money = (v: number) => `$${Math.round(v).toLocaleString("en-US")}`;
  const saved = Math.max(0, (total - GROWIXA) * 12);

  return (
    <>
      <PageHero
        hue="send"
        title="What are you paying for the stack you already have?"
        lede="Tick everything you subscribe to. We'll add it up at list price and show which stage of the engine replaces each one. No email required, nothing saved."
      />

      <Sec hue="send">
        <div className={own.calc}>
          <div>
            {STACK.map(([hue, title, tools]) => (
              <div
                key={title}
                className={own.group}
                style={
                  {
                    "--hue": `var(--${hue})`,
                    "--hue-l": `var(--${hue}-l)`,
                    "--hue-d": `var(--${hue}-d)`,
                  } as React.CSSProperties
                }
              >
                <div className={own.gh}>
                  <i aria-hidden="true" />
                  {title}
                </div>
                <div className={own.tools}>
                  {tools.map(([name, price]) => (
                    <label key={name} className={own.tick}>
                      <input
                        type="checkbox"
                        checked={!!picked[name]}
                        onChange={(e) => setPicked((p) => ({ ...p, [name]: e.target.checked }))}
                      />
                      <span className={own.bx} aria-hidden="true">
                        <svg width="11" height="11" viewBox="0 0 14 14" fill="none">
                          <path
                            d="M2.6 7.2l3 3 5.8-6.4"
                            stroke="#fff"
                            strokeWidth="2.4"
                            strokeLinecap="round"
                            strokeLinejoin="round"
                          />
                        </svg>
                      </span>
                      <span className={own.lb}>{name}</span>
                      <span className={own.pr}>${price}</span>
                    </label>
                  ))}
                </div>
              </div>
            ))}
            <p className={own.disclaimer}>
              Public list prices for an entry paid tier at roughly 10,000 contacts, as of August
              2026. Your actual bill will differ — this is a starting point, not an invoice.
            </p>
          </div>

          <div className={own.out2}>
            <div className={own.outHead}>Your stack today</div>
            <div className={own.big}>
              <span className={own.bigV}>{money(total)}</span>
              <span className={own.bigK}>{count} tools, per month</span>
            </div>
            <div className={own.line}>
              <span>Per year</span>
              <b>{money(total * 12)}</b>
            </div>
            <div className={own.line}>
              <span>Growixa Growth</span>
              <b style={{ color: "var(--create-d)" }}>${GROWIXA}</b>
            </div>
            <div className={own.line}>
              <span>Logins to manage</span>
              <b>{count} → 1</b>
            </div>
            <div className={own.saved}>
              <span className={own.savedV}>{money(saved)}</span>
              <span className={own.savedK}>saved a year</span>
            </div>
          </div>
        </div>
      </Sec>

      <ClosingCta
        title="One login instead of that."
        body="Start on the free plan and move the pieces across as you go. Nothing needs migrating on day one."
        primary={{ to: "/register", label: "Start free" }}
        secondary={{ to: "/sandbox", label: "Try it first" }}
      />
    </>
  );
}
