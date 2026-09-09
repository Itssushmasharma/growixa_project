import Link from "next/link";
import styles from "./classic-home.module.css";

const FEATURES = [
  [
    "◎",
    "Audience intelligence",
    "Organize contacts, lists and behavior-based segments in one reliable workspace.",
  ],
  [
    "✉",
    "Email campaigns",
    "Create, review, schedule and measure campaigns with suppression protection built in.",
  ],
  [
    "✦",
    "AI Content Studio",
    "Generate brand-aware drafts, then edit and approve before anything goes out.",
  ],
  [
    "◫",
    "Marketing calendar",
    "See campaigns and scheduled social content together before you publish.",
  ],
  [
    "✓",
    "Human approvals",
    "Keep consequential actions under team control with clear review states.",
  ],
  [
    "↗",
    "Actionable analytics",
    "Move from what happened to why it matters and what to improve next.",
  ],
] as const;

export const FAQS = [
  [
    "Can I start without a credit card?",
    "Yes. Create a workspace and explore the available free plan before choosing a paid plan.",
  ],
  [
    "Does AI publish automatically?",
    "No. Growixa keeps a human review and approval step before consequential external actions.",
  ],
  [
    "Can I import my existing contacts?",
    "Yes. Growixa supports CSV contact import, field mapping, lists, segments and suppression handling.",
  ],
  [
    "Which marketing channels are available?",
    "Email campaign workflows are available now. Social publishing depends on the integrations enabled for your workspace.",
  ],
] as const;

export function ClassicHome() {
  return (
    <div className={styles.page}>
      <section className={styles.hero}>
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
            kicker="PLATFORM"
            title="Everything your marketing team needs to move"
            copy="Powerful enough for real execution, simple enough to understand without training."
          />
          <div className={styles.featureGrid}>
            {FEATURES.map(([icon, title, copy]) => (
              <article key={title}>
                <span className={styles.featureIcon}>{icon}</span>
                <h3>{title}</h3>
                <p>{copy}</p>
                <Link href="/platform">Learn more →</Link>
              </article>
            ))}
          </div>
        </div>
      </section>

      <section className={styles.split}>
        <div className={styles.wrap}>
          <div className={styles.splitGrid}>
            <MiniCalendar />
            <div className={styles.splitCopy}>
              <span className={styles.kicker}>BUILT FOR CLARITY</span>
              <h2>See the whole campaign before it goes live.</h2>
              <p>
                Bring email, social content and campaign milestones into one planning surface.
                Filter by status, channel and owner so your team always knows what is ready.
              </p>
              <ul>
                <li>Unified campaign planning</li>
                <li>Explicit approval states</li>
                <li>Clear publishing status</li>
                <li>Responsive team workspace</li>
              </ul>
              <Link className={styles.primary} href="/register">
                Create your workspace →
              </Link>
            </div>
          </div>
        </div>
      </section>

      <section className={styles.pricing}>
        <div className={styles.wrap}>
          <SectionHead
            kicker="SIMPLE PLANS"
            title="Start small. Upgrade when growth demands it."
            copy="Choose the plan that fits your contact, email and AI usage."
          />
          <div className={styles.priceGrid}>
            {[
              ["Free", "Explore Growixa", "For evaluating the workflow"],
              ["Starter", "Launch campaigns", "For small teams getting consistent"],
              ["Pro", "Scale execution", "For growing marketing operations"],
            ].map(([name, title, copy], i) => (
              <article key={name} className={i === 1 ? styles.featuredPlan : undefined}>
                {i === 1 && <span className={styles.popular}>POPULAR</span>}
                <span className={styles.planName}>{name}</span>
                <h3>{title}</h3>
                <p>{copy}</p>
                <ul>
                  <li>Campaign workspace</li>
                  <li>Audience management</li>
                  <li>Team approval controls</li>
                </ul>
                <Link href="/pricing">View current pricing →</Link>
              </article>
            ))}
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
                aria-label="Campaign performance trend"
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
