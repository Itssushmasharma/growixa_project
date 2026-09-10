"use client";

import { useState } from "react";
import Image from "next/image";
import Link from "next/link";
import styles from "./classic-home.module.css";
import { GrowthChartTerminal } from "@/components/chart-terminal";

import { FEATURES, FAQS } from "./classic-home-data";

export function ClassicHome() {
  const [splitPreview, setSplitPreview] = useState<"automation" | "calendar">("automation");

  return (
    <div className={styles.page}>
      <section className={styles.hero}>
        <span className={styles.heroWatermark} aria-hidden="true">
          GROWIXA
        </span>
        <div className={styles.heroGlow} aria-hidden="true" />
        <div className={styles.wrap}>
          <div className={styles.badge}>AI-POWERED MARKETING EXECUTION</div>
          <h1>
            Turn marketing goals into
            <br /> <em>approved growth campaigns.</em>
          </h1>
          <p className={styles.heroCopy}>
            Growixa brings audience data, brand-aware content, campaign execution and actionable
            insights into one clear workspace—so your team always knows the next best action.
          </p>
          <div className={styles.actions}>
            <Link className={styles.primary} href="/register">
              Start free <span>→</span>
            </Link>
            <Link className={styles.secondary} href="#how-it-works">
              See how it works
            </Link>
          </div>
          <p className={styles.assurance}>
            No credit card required · Human approval before publishing · Your draft stays yours
          </p>
          <div className={styles.tactileDeck} aria-label="Engine Capabilities">
            <span className={[styles.tactilePill, styles.pillUi].join(" ")}>UI Engine</span>
            <span className={[styles.tactilePill, styles.pillUx].join(" ")}>UX Automation</span>
            <span className={[styles.tactilePill, styles.pillGrowth].join(" ")}>3D Growth</span>
            <span className={[styles.tactilePill, styles.pillAudience].join(" ")}>Audience AI</span>
          </div>
          <ProductPreview />
        </div>
      </section>

      <section className={styles.intro} aria-labelledby="connected-heading">
        <div className={styles.narrow}>
          <span className={styles.kicker}>ONE CONNECTED GROWTH SYSTEM</span>
          <h2 id="connected-heading">Know what to do. Get it approved. Improve what works.</h2>
          <p>
            Replace disconnected marketing tools with one understandable loop that connects your
            goal, audience, message, human approval, execution and learning.
          </p>
          <div className={styles.trustRow}>
            {[
              ["01", "Plan"],
              ["02", "Create"],
              ["03", "Approve"],
              ["04", "Execute"],
              ["05", "Measure"],
              ["06", "Improve"],
            ].map(([number, label]) => (
              <span key={label}>
                <small>{number}</small>
                {label}
              </span>
            ))}
          </div>
        </div>
      </section>

      <section className={styles.steps} id="how-it-works">
        <div className={styles.wrap}>
          <SectionHead
            kicker="GET STARTED"
            title="From goal to campaign in three clear steps"
            copy="Every screen tells your team what matters and what to do next."
          />
          <div className={styles.stepGrid}>
            {[
              [
                "01",
                "Set up your workspace",
                "Add your brand voice, sender identity and team permissions.",
              ],
              [
                "02",
                "Choose a growth goal",
                "Select your audience and let Growixa shape the campaign plan.",
              ],
              [
                "03",
                "Review and execute",
                "Approve content, schedule safely and measure the result.",
              ],
            ].map(([n, t, d]) => (
              <article key={n}>
                <span>{n}</span>
                <h3>{t}</h3>
                <p>{d}</p>
              </article>
            ))}
          </div>
        </div>
      </section>

      <section className={styles.features} id="features">
        <div className={styles.wrap}>
          <SectionHead
            kicker="PLATFORM CAPABILITIES"
            title="Everything your marketing team needs to move fast & scale"
            copy="Powerful enough for real execution, simple enough for your entire team to operate without training."
          />
          <div className={styles.featureGrid}>
            {FEATURES.map((item) => (
              <article key={item.title} className={styles.featureCard}>
                <div className={styles.featureTopRow}>
                  <span className={styles.featureIcon}>{item.icon}</span>
                  <span className={styles.featureTag}>{item.tag}</span>
                </div>
                <h3>{item.title}</h3>
                <p>{item.copy}</p>
                <Link href="/platform">
                  Learn more <span>→</span>
                </Link>
              </article>
            ))}
          </div>
        </div>
      </section>

      <section
        className={styles.terminalSection}
        id="growth-terminal"
        aria-label="Institutional Growth Telemetry & Chart Analysis"
      >
        <div className={styles.wrap}>
          <SectionHead
            kicker="INSTITUTIONAL TELEMETRY"
            title="Institutional Growth Telemetry & Chart Analysis Terminal"
            copy="Analyze campaign velocity, conversion depth, and deliverability with precision candlestick charting, technical indicators, and real-time execution telemetry."
          />
          <GrowthChartTerminal initialMetric="GROWTH_VELOCITY" initialTimeframe="24H" />
        </div>
      </section>

      <section className={styles.split}>
        <div className={styles.wrap}>
          <div className={styles.splitGrid}>
            <div className={styles.splitVisualCol}>
              <div
                className={styles.previewToggleRow}
                role="group"
                aria-label="Campaign Preview Mode"
              >
                <button
                  type="button"
                  onClick={() => setSplitPreview("automation")}
                  className={`${styles.previewToggleBtn} ${splitPreview === "automation" ? styles.previewToggleBtnActive : ""}`}
                >
                  ⚡ 3D Automation Engine
                </button>
                <button
                  type="button"
                  onClick={() => setSplitPreview("calendar")}
                  className={`${styles.previewToggleBtn} ${splitPreview === "calendar" ? styles.previewToggleBtnActive : ""}`}
                >
                  📅 Campaign Timeline
                </button>
              </div>

              {splitPreview === "automation" ? (
                <div className={styles.automation3DCard}>
                  <div className={styles.visualCardBadge}>
                    <span className={styles.badgeLiveDot} />
                    <span>AUTONOMOUS ENGINE · LIVE WORKFLOW</span>
                  </div>
                  <Image
                    src="/assets/3d/growixa_3d_tactile_automation.jpg"
                    alt="Marketing Automation 3D Workflow"
                    width={600}
                    height={420}
                    unoptimized
                  />
                  <div className={styles.visualCardCaption}>
                    <strong>Tactile multi-step automation</strong>
                    <p>
                      Orchestrate email sequences, condition-based branching, and real-time
                      verification.
                    </p>
                  </div>
                </div>
              ) : (
                <MiniCalendar />
              )}
            </div>

            <div className={styles.splitCopy}>
              <span className={styles.kicker}>BUILT FOR CLARITY</span>
              <h2>See the whole campaign before it goes live.</h2>
              <p>
                Bring email sequences, social content, and campaign milestones into one planning
                surface. Filter by status, channel, and owner so your team always knows what is
                ready, what is approved, and what performs best.
              </p>
              <ul>
                <li>Unified campaign planning &amp; timeline</li>
                <li>Explicit deterministic approval states</li>
                <li>Clear publishing &amp; deliverability status</li>
                <li>Responsive team collaboration workspace</li>
              </ul>
              <Link className={styles.primary} href="/register">
                Create your workspace →
              </Link>
            </div>
          </div>
        </div>
      </section>

      <section className={styles.pricing} id="pricing">
        <div className={styles.wrap}>
          <SectionHead
            kicker="SIMPLE PLANS"
            title="Start small. Upgrade when growth demands it."
            copy="Choose the plan that fits your contact, email and AI usage. Transparent pricing built to scale."
          />
          <div className={styles.priceGrid}>
            <article className={styles.planCard}>
              <div className={styles.planBadgeRow}>
                <span className={styles.planName}>FREE</span>
                <span className={styles.planTierTag}>FOREVER</span>
              </div>
              <h3>Explore Growixa</h3>
              <p>Everything you need to verify contacts and launch your first campaign.</p>
              <div className={styles.priceAmountRow}>
                <span className={styles.priceCurrency}>$</span>
                <span className={styles.priceValue}>0</span>
                <span className={styles.pricePeriod}>/ month</span>
              </div>
              <ul className={styles.planFeatureList}>
                <li>
                  <strong>1,000</strong> contacts
                </li>
                <li>
                  <strong>2,000</strong> emails / month
                </li>
                <li>
                  <strong>1</strong> sending domain
                </li>
                <li>Campaigns &amp; templates studio</li>
                <li>Human-in-the-loop approvals</li>
              </ul>
              <Link className={styles.planCtaOutline} href="/register">
                Start free forever →
              </Link>
              <Link className={styles.planDetailsLink} href="/pricing">
                View current pricing →
              </Link>
            </article>

            <article className={`${styles.planCard} ${styles.featuredPlan}`}>
              <div className={styles.planBadgeRow}>
                <span className={styles.planName}>STARTER</span>
                <span className={styles.popular}>POPULAR</span>
              </div>
              <h3>Launch Campaigns</h3>
              <p>For founders and small growth teams driving consistent outbound.</p>
              <div className={styles.priceAmountRow}>
                <span className={styles.priceCurrency}>$</span>
                <span className={styles.priceValue}>29</span>
                <span className={styles.pricePeriod}>/ month</span>
              </div>
              <ul className={styles.planFeatureList}>
                <li>
                  <strong>5,000</strong> contacts
                </li>
                <li>
                  <strong>25,000</strong> emails / month
                </li>
                <li>
                  <strong>3</strong> sending domains + warm-up
                </li>
                <li>Sequences &amp; automated follow-ups</li>
                <li>
                  <strong>500</strong> Find lead credits / month
                </li>
              </ul>
              <Link className={styles.planCtaPrimary} href="/register">
                Choose Starter →
              </Link>
              <Link className={styles.planDetailsLink} href="/pricing">
                View current pricing →
              </Link>
            </article>

            <article className={styles.planCard}>
              <div className={styles.planBadgeRow}>
                <span className={styles.planName}>GROWTH</span>
                <span className={styles.planTierTag}>SCALE AI</span>
              </div>
              <h3>Scale Execution</h3>
              <p>The complete engine with brand-voice AI studio and high volume.</p>
              <div className={styles.priceAmountRow}>
                <span className={styles.priceCurrency}>$</span>
                <span className={styles.priceValue}>89</span>
                <span className={styles.pricePeriod}>/ month</span>
              </div>
              <ul className={styles.planFeatureList}>
                <li>
                  <strong>25,000</strong> contacts
                </li>
                <li>
                  <strong>150,000</strong> emails / month
                </li>
                <li>
                  <strong>Unlimited</strong> sending domains
                </li>
                <li>Full AI Studio with brand voice guardrails</li>
                <li>
                  <strong>2,500</strong> Find credits + Chart Terminal
                </li>
              </ul>
              <Link className={styles.planCtaOutline} href="/register">
                Choose Growth →
              </Link>
              <Link className={styles.planDetailsLink} href="/pricing">
                View current pricing →
              </Link>
            </article>
          </div>

          <div className={styles.pricingEnterpriseBanner}>
            <div>
              <strong>Need custom enterprise scale, dedicated IP pools, or custom SLAs?</strong>
              <p>
                We provide dedicated SMTP infrastructure, SSO/SAML, and custom volume contracts.
              </p>
            </div>
            <Link className={styles.enterpriseBtn} href="/contact">
              Talk to enterprise sales →
            </Link>
          </div>
        </div>
      </section>

      <section className={styles.faq}>
        <div className={styles.wrap}>
          <div className={styles.faqGrid}>
            <div>
              <span className={styles.kicker}>FAQ</span>
              <h2>Questions, answered clearly.</h2>
              <p>Need help choosing a workflow or plan?</p>
              <Link href="/contact">Talk to a Growixa specialist →</Link>
            </div>
            <div className={styles.faqList}>
              {FAQS.map(([q, a], i) => (
                <details key={q} open={i === 0}>
                  <summary>
                    {q}
                    <span>+</span>
                  </summary>
                  <p>{a}</p>
                </details>
              ))}
            </div>
          </div>
        </div>
      </section>

      <section className={styles.finalCta}>
        <div className={styles.finalGlow} aria-hidden="true" />
        <div className={styles.narrow}>
          <span className={styles.kicker}>START GROWING</span>
          <h2>
            Bring your marketing together.
            <br />
            Move with confidence.
          </h2>
          <p>
            Create your Growixa workspace and turn your next goal into an approved, measurable
            campaign.
          </p>
          <div className={styles.actions}>
            <Link className={styles.primary} href="/register">
              Start free →
            </Link>
            <Link className={styles.secondary} href="/contact">
              Talk to us
            </Link>
          </div>
        </div>
      </section>
    </div>
  );
}

function SectionHead({ kicker, title, copy }: { kicker: string; title: string; copy: string }) {
  return (
    <div className={styles.sectionHead}>
      <span className={styles.kicker}>{kicker}</span>
      <h2>{title}</h2>
      <p>{copy}</p>
    </div>
  );
}

function ProductPreview() {
  return (
    <div className={styles.productScene}>
      <div className={styles.sceneOrb} aria-hidden="true" />
      <div className={[styles.motionChip, styles.goalChip].join(" ")} aria-hidden="true">
        <span>GOAL</span>
        <strong>Generate qualified leads</strong>
      </div>
      <div className={[styles.motionChip, styles.aiChip].join(" ")} aria-hidden="true">
        <i>✦</i>
        <span>AI draft ready</span>
      </div>
      <div className={[styles.motionChip, styles.approvalChip].join(" ")} aria-hidden="true">
        <i>✓</i>
        <span>Human approved</span>
      </div>
      <div className={[styles.motionChip, styles.insightChip].join(" ")} aria-hidden="true">
        <span>NEXT ACTION</span>
        <strong>Optimize the campaign</strong>
      </div>
      <div className={styles.sceneWith3DFluid}>
        <div className={styles.product}>
          <div className={styles.productBar}>
            <div>
              <i />
              <i />
              <i />
            </div>
            <span>Growixa · Illustrative product preview</span>
            <b>SS</b>
          </div>
          <div className={styles.productBody}>
            <aside>
              <strong>G</strong>
              {["Overview", "Audience", "Campaigns", "Content", "Calendar"].map((x, i) => (
                <span className={i === 0 ? styles.activeNav : undefined} key={x}>
                  {x}
                </span>
              ))}
            </aside>
            <main>
              <header>
                <div>
                  <small>GOOD MORNING</small>
                  <h3>What do you want to grow today?</h3>
                </div>
                <Link className={styles.previewButton} href="/register">
                  Create campaign
                </Link>
              </header>
              <div className={styles.metrics}>
                {[
                  ["AUDIENCE", "Organized"],
                  ["CAMPAIGN", "Planned"],
                  ["CONTENT", "Reviewed"],
                  ["INSIGHTS", "Actionable"],
                ].map(([l, v]) => (
                  <article key={l}>
                    <span>{l}</span>
                    <strong>{v}</strong>
                    <small>Connected workflow</small>
                  </article>
                ))}
              </div>
              <div className={styles.previewGrid}>
                <article className={styles.chart}>
                  <span>Campaign performance</span>
                  <svg
                    viewBox="0 0 500 150"
                    preserveAspectRatio="none"
                    aria-label="Illustrative campaign performance trend"
                  >
                    <path d="M0 125 C70 120 70 80 140 90 S230 40 300 65 S390 20 500 30" />
                    <path
                      className={styles.area}
                      d="M0 125 C70 120 70 80 140 90 S230 40 300 65 S390 20 500 30 L500 150 L0 150 Z"
                    />
                  </svg>
                </article>
                <article className={styles.nextAction}>
                  <span>BEST NEXT ACTION</span>
                  <strong>Review 3 campaign drafts</strong>
                  <p>Content is ready for your approval.</p>
                  <Link className={styles.previewAction} href="/register">
                    Open approval queue
                  </Link>
                </article>
              </div>
            </main>
          </div>
        </div>

        <aside className={styles.fluidCardContainer}>
          <span className={styles.fluidBadge}>✦ 3D FLUID ENGINE</span>
          <div className={styles.fluidImageWrapper}>
            <Image
              src="/assets/3d/growixa_3d_fluid_core.jpg"
              alt="Growixa 3D Dynamic Fluid Ribbon Core"
              width={340}
              height={380}
              unoptimized
            />
          </div>
          <div className={styles.fluidInfo}>
            <h4>Dynamic 3D Flow</h4>
            <p>Conveying continuous depth, energy and automated campaign momentum.</p>
          </div>
        </aside>
      </div>
      <div className={styles.motionTrack} aria-hidden="true">
        <span>Goal</span>
        <i />
        <span>Audience</span>
        <i />
        <span>Create</span>
        <i />
        <span>Approve</span>
        <i />
        <span>Measure</span>
      </div>
      <p className={styles.motionNote}>
        One connected flow from business goal to measurable next action.
      </p>
    </div>
  );
}

function MiniCalendar() {
  return (
    <div className={styles.calendar}>
      <div className={styles.calendarTop}>
        <div>
          <small>SEPTEMBER 2026</small>
          <strong>Marketing calendar</strong>
        </div>
        <Link href="/register">+ New campaign</Link>
      </div>
      <div className={styles.days}>
        {["MON", "TUE", "WED", "THU", "FRI"].map((x) => (
          <span key={x}>{x}</span>
        ))}
      </div>
      <div className={styles.calendarGrid}>
        {Array.from({ length: 15 }, (_, i) => (
          <div key={i}>
            <small>{i + 7}</small>
            {i === 2 && <span className={styles.emailEvent}>Email · Launch</span>}
            {i === 6 && <span className={styles.socialEvent}>Social · LinkedIn</span>}
            {i === 12 && <span className={styles.reviewEvent}>Review · Q4</span>}
          </div>
        ))}
      </div>
    </div>
  );
}
