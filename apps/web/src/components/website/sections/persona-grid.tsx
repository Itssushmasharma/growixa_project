import React from "react";
import styles from "./persona-grid.module.css";
import { Users, Briefcase, PenTool, TrendingUp, BarChart3, ShieldAlert } from "lucide-react";

interface RoleCard {
  letter: string;
  role: string;
  icon: React.ReactNode;
  desc: string;
  tags: string[];
  styleClass: string;
}

const ROLES: RoleCard[] = [
  {
    letter: "M",
    role: "Marketing Manager",
    icon: <Briefcase className="w-5 h-5" />,
    desc: "Oversee multi-channel social and email campaigns, approve AI copy proposals, and align brand voice.",
    tags: ["Campaign Approvals", "Brand Voice", "Multi-Channel"],
    styleClass: styles.q1 ?? "",
  },
  {
    letter: "C",
    role: "Content Creator",
    icon: <PenTool className="w-5 h-5" />,
    desc: "Generate social media copy, schedule Instagram/LinkedIn posts, and manage media upload assets.",
    tags: ["AI Assistant", "Post Scheduler", "Media Manager"],
    styleClass: styles.q2 ?? "",
  },
  {
    letter: "G",
    role: "Growth Lead",
    icon: <TrendingUp className="w-5 h-5" />,
    desc: "Scale audience list segments, configure Postmark email relays, and optimize conversion funnels.",
    tags: ["Segment Targeting", "Email Relays", "Funnel Scale"],
    styleClass: styles.q3 ?? "",
  },
  {
    letter: "A",
    role: "Analytics Lead",
    icon: <BarChart3 className="w-5 h-5" />,
    desc: "Track real-time open/click delivery webhooks, monitor quota usages, and measure ROI.",
    tags: ["Webhook Telemetry", "Candlestick Charts", "Quota Gauges"],
    styleClass: styles.q4 ?? "",
  },
];

export function PersonaGridSection() {
  return (
    <section className={styles.section} id="personas">
      <div className={styles.header}>
        <div className={styles.eyebrow}>
          <Users className="w-4 h-4" /> Role-Tailored Workflows
        </div>
        <h2 className={styles.title}>
          No Matter The Goal, <span>Growixa Fits Your Team</span>
        </h2>
        <p className={styles.subtitle}>
          Custom role permissions and specialized views built for every growth stakeholder in your organization.
        </p>
      </div>

      {/* 4-Quadrant Infographic Stage with Central Ring (Reference Image Layout) */}
      <div className={styles.infographicStage}>
        {/* Central Circular Ring Hub */}
        <div className={styles.centerRing}>
          <span className={styles.centerRingTitle}>Team Roles</span>
          <span className={styles.centerRingSub}>Growixa Stakeholders</span>
        </div>

        {/* 2x2 Interlocking Quadrant Grid */}
        <div className={styles.quadrantGrid}>
          {ROLES.map((r) => (
            <div key={r.letter} className={`${styles.quadrantCard} ${r.styleClass}`}>
              <div className={styles.badgeNode}>
                {r.letter}
              </div>

              <div>
                <h3 className={styles.roleTitle}>{r.role}</h3>
                <p className={styles.roleDesc}>{r.desc}</p>
              </div>

              <div className={styles.tagContainer}>
                {r.tags.map((tag, tIdx) => (
                  <span key={tIdx} className={styles.tagPill}>
                    {tag}
                  </span>
                ))}
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Platform Admin Banner below */}
      <div className={styles.adminBanner}>
        <div className={styles.adminLeft}>
          <div className={styles.adminAvatar}>
            <ShieldAlert className="w-6 h-6" />
          </div>
          <div>
            <h4 className={styles.adminTitle}>Platform Admin & Security Control</h4>
            <p className={styles.adminDesc}>
              Manage customer subscriptions, Razorpay credit top-ups, default AI provider keys, and immutable audit logs.
            </p>
          </div>
        </div>

        <div className={styles.tagContainer}>
          <span className={`${styles.tagPill} bg-stone-100 text-stone-800 border-stone-200`}>
            Razorpay Billing
          </span>
          <span className={`${styles.tagPill} bg-stone-100 text-stone-800 border-stone-200`}>
            Audit Logging
          </span>
          <span className={`${styles.tagPill} bg-stone-100 text-stone-800 border-stone-200`}>
            BYO AI Config
          </span>
        </div>
      </div>
    </section>
  );
}
