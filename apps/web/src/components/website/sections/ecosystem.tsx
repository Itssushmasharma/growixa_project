import React from "react";
import styles from "./ecosystem.module.css";
import { 
  Mail, 
  Cpu, 
  Bot, 
  CreditCard, 
  Globe, 
  Share2, 
  MessageSquare, 
  Zap, 
  ShieldCheck 
} from "lucide-react";

interface IntegrationItem {
  name: string;
  category: string;
  desc: string;
  icon: React.ReactNode;
  badge: string;
}

const INTEGRATIONS: IntegrationItem[] = [
  {
    name: "Postmark",
    category: "Email Relay",
    desc: "Transactional email delivery with real-time open, click, and bounce webhooks.",
    icon: <Mail className="w-6 h-6" />,
    badge: "Native Relay",
  },
  {
    name: "OpenAI",
    category: "LLM Provider",
    desc: "GPT-4o & Reasoning AI models for multi-channel copy generation and optimization.",
    icon: <Cpu className="w-6 h-6" />,
    badge: "BYO & Platform Default",
  },
  {
    name: "Claude AI",
    category: "LLM Provider",
    desc: "Anthropic Claude 3.5 Sonnet for long-form brand content and audience insights.",
    icon: <Bot className="w-6 h-6" />,
    badge: "Native Adapter",
  },
  {
    name: "Stripe",
    category: "Payment Gateway",
    desc: "Global subscription billing, automated invoicing, and credit top-up orders.",
    icon: <CreditCard className="w-6 h-6" />,
    badge: "Global Checkout",
  },
  {
    name: "Razorpay",
    category: "Payment Gateway",
    desc: "Dual-currency INR & international subscription checkout with webhook signatures.",
    icon: <ShieldCheck className="w-6 h-6" />,
    badge: "Instant Top-Up",
  },
  {
    name: "Google Workspace",
    category: "Identity & Email",
    desc: "OAuth 2.0 authentication, domain verification, and team directory sync.",
    icon: <Globe className="w-6 h-6" />,
    badge: "SSO Ready",
  },
  {
    name: "Meta Ads",
    category: "Social & Ads",
    desc: "Instagram & Facebook direct media publishing, campaign metrics, and audience sync.",
    icon: <Share2 className="w-6 h-6" />,
    badge: "Direct Connect",
  },
  {
    name: "LinkedIn",
    category: "Professional Social",
    desc: "Scheduled post publishing, engagement telemetry, and corporate brand pages.",
    icon: <Share2 className="w-6 h-6" />,
    badge: "OAuth 2.0",
  },
  {
    name: "Slack",
    category: "Team Alerts",
    desc: "Instant channel alerts for campaign dispatches, audit logs, and lead notifications.",
    icon: <MessageSquare className="w-6 h-6" />,
    badge: "Real-Time",
  },
  {
    name: "Zapier",
    category: "Workflow Automation",
    desc: "2,000+ app triggers to sync contacts, trigger campaigns, and pass conversion events.",
    icon: <Zap className="w-6 h-6" />,
    badge: "Webhook Ready",
  },
];

export function EcosystemSection() {
  return (
    <section className={styles.section} id="ecosystem">
      <div className={styles.header}>
        <div className={styles.eyebrow}>
          <Zap className="w-4 h-4" /> Native Integrations
        </div>
        <h2 className={styles.title}>
          Ecosystem — Connects With Your <span>Tech Stack</span>
        </h2>
        <p className={styles.subtitle}>
          Native integrations with leading email relays, payment gateways, LLMs, and social platforms.
        </p>
      </div>

      <div className={styles.grid}>
        {INTEGRATIONS.map((item, idx) => (
          <div key={idx} className={styles.card}>
            <div>
              <div className={styles.cardTop}>
                <div className={styles.iconWrapper}>{item.icon}</div>
                <span className={styles.badge}>{item.badge}</span>
              </div>
              <div className={styles.category}>{item.category}</div>
              <h3 className={styles.name}>{item.name}</h3>
              <p className={styles.desc}>{item.desc}</p>
            </div>
          </div>
        ))}
      </div>
    </section>
  );
}
