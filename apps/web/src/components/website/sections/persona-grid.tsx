import React from "react";
import styles from "./persona-grid.module.css";
import { Users, Briefcase, PenTool, TrendingUp, BarChart3, ShieldAlert } from "lucide-react";

interface RoleCard {
  role: string;
  icon: React.ReactNode;
  desc: string;
  tags: string[];
}

const ROLES: RoleCard[] = [
  {
    role: "Marketing Manager",
    icon: <Briefcase className="w-5 h-5" />,
    desc: "Oversee multi-channel social and email campaigns, approve AI copy proposals, and align brand voice.",
    tags: ["Campaign Approvals", "Brand Voice", "Multi-Channel"],
  },
  {
    role: "Content Creator",
    icon: <PenTool className="w-5 h-5" />,
    desc: "Generate social media copy, schedule Instagram/LinkedIn posts, and manage media upload assets.",
    tags: ["AI Assistant", "Post Scheduler", "Media Manager"],
  },
  {
    role: "Growth Lead",
    icon: <TrendingUp className="w-5 h-5" />,
    desc: "Scale audience list segments, configure Postmark email relays, and optimize conversion funnels.",
    tags: ["Segment Targeting", "Email Relays", "Funnel Scale"],
  },
  {
    role: "Analytics Lead",
    icon: <BarChart3 className="w-5 h-5" />,
    desc: "Track real-time open/click delivery webhooks, monitor quota usages, and measure ROI.",
    tags: ["Webhook Telemetry", "Candlestick Charts", "Quota Gauges"],
  },
  {
    role: "Platform Admin",
    icon: <ShieldAlert className="w-5 h-5" />,
    desc: "Manage customer subscriptions, Razorpay credit top-ups, default AI provider keys, and audit logs.",
    tags: ["Razorpay Billing", "Audit Logging", "BYO AI Config"],
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

      <div className={styles.grid}>
        {ROLES.map((r, idx) => (
          <div key={idx} className={styles.card}>
            <div className={styles.roleHeader}>
              <div className={styles.roleAvatar}>{r.icon}</div>
              <h3 className={styles.roleName}>{r.role}</h3>
            </div>
            <p className={styles.roleDesc}>{r.desc}</p>
            <div className={styles.pillContainer}>
              {r.tags.map((tag, tIdx) => (
                <span key={tIdx} className={styles.pill}>
                  {tag}
                </span>
              ))}
            </div>
          </div>
        ))}
      </div>
    </section>
  );
}
