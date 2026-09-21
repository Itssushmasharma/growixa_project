import React from "react";
import Link from "next/link";
import styles from "./integration-hub-orb.module.css";
import { 
  Network, 
  Search, 
  ArrowRight, 
  Mail, 
  Cpu, 
  CreditCard, 
  Globe, 
  MessageSquare, 
  Zap,
  Sparkles,
  Share2,
  Lock
} from "lucide-react";

export function IntegrationHubOrbSection() {
  const APPS = [
    { name: "Postmark", icon: Mail, left: "6%", top: "68%" },
    { name: "OpenAI", icon: Cpu, left: "17%", top: "45%" },
    { name: "Razorpay", icon: CreditCard, left: "28%", top: "28%" },
    { name: "Claude AI", icon: Sparkles, left: "39%", top: "18%" },
    { name: "Growixa Hub", icon: Network, left: "50%", top: "12%" },
    { name: "Google", icon: Globe, left: "61%", top: "18%" },
    { name: "Meta Ads", icon: Share2, left: "72%", top: "28%" },
    { name: "Slack", icon: MessageSquare, left: "83%", top: "45%" },
    { name: "Zapier", icon: Zap, left: "94%", top: "68%" },
  ];

  return (
    <section className={styles.section} id="integration-hub">
      <div className={styles.header}>
        <div className={styles.eyebrow}>
          <Network className="w-4 h-4" /> Central Ecosystem Architecture
        </div>
        <h2 className={styles.title}>
          A Data & Growth Solution That Works For <span>Your Ecosystem</span>
        </h2>
        <p className={styles.subtitle}>
          Growixa&apos;s API connectors allow you to integrate your email relays, payment gateways, LLMs, and SaaS apps quickly and agent-free.
        </p>
      </div>

      {/* Top Category Header Bar matching Reference Image Left & Right Labels */}
      <div className={styles.categoryHeaderBar}>
        <div className={styles.catCol}>
          <div className={styles.catTitle}>Core Infrastructure</div>
          <div className={styles.catSub}>Email Relays, DBs & Storage Connectors</div>
        </div>

        <div className={styles.connectorLineBar} />

        <div className={`${styles.catCol} ${styles.catColRight}`}>
          <div className={styles.catTitle}>Growth & AI Engines</div>
          <div className={styles.catSub}>LLMs, Social Automation & Webhooks</div>
        </div>
      </div>

      {/* Curved Arch Stage matching Reference Image Layout */}
      <div className={styles.arcStage}>
        {/* Curved SVG Arch Line Guide */}
        <svg className={styles.archGuideSvg} viewBox="0 0 1100 380">
          <path 
            className={styles.archPath} 
            d="M 60,300 Q 550,-30 1040,300" 
          />
        </svg>

        {/* Floating App Cards Along Parabolic Arch */}
        <div className={styles.appArchList}>
          {APPS.map((app) => {
            const Icon = app.icon;
            return (
              <div 
                key={app.name} 
                className={styles.appCardPill}
                style={{ left: app.left, top: app.top }}
              >
                <div className={styles.appIconBox}>
                  <Icon className="w-5 h-5" />
                </div>
                <span className={styles.appLabel}>{app.name}</span>
              </div>
            );
          })}
        </div>

        {/* Central Glowing Dome (Bottom Sphere from Reference Image) */}
        <div className={styles.centralDome}>
          <h3 className={styles.domeTitle}>Growixa Core</h3>
          <span className={styles.domeSubtitle}>Unified Growth Mesh Engine</span>
        </div>
      </div>

      {/* Search Bar Mockup Card */}
      <div className={styles.searchMockCard}>
        <div className={styles.searchInputText}>
          <Search className="w-5 h-5 text-amber-700" />
          <span>Search 10+ native integrations (Postmark, Razorpay, OpenAI, Claude)...</span>
        </div>
        <Link href="/login" className={styles.bookDemoBtn}>
          Book Demo <ArrowRight className="w-4 h-4 inline-block ml-1" />
        </Link>
      </div>
    </section>
  );
}
