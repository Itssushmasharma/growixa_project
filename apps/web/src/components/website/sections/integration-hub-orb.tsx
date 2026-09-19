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
  Share2, 
  MessageSquare, 
  Zap, 
  ShieldCheck 
} from "lucide-react";

export function IntegrationHubOrbSection() {
  return (
    <section className={styles.section} id="integration-hub">
      <div className={styles.header}>
        <div className={styles.eyebrow}>
          <Network className="w-4 h-4" /> Central Integration Hub
        </div>
        <h2 className={styles.title}>
          A Data & Growth Solution That Works For <span>Your Ecosystem</span>
        </h2>
        <p className={styles.subtitle}>
          Growixa&apos;s API connectors allow you to integrate your email relays, payment gateways, LLMs, and SaaS apps quickly and agent-free.
        </p>
      </div>

      {/* Central Glowing Purple Orb with Ribbon Badges matching Image 2 & Image 5 */}
      <div className={styles.orbContainer}>
        <div className={styles.ribbon}>
          <div className={styles.ribbonItem}>
            <Mail className={`${styles.ribbonIcon} text-amber-400`} />
            <span className={styles.ribbonText}>Postmark</span>
          </div>

          <div className={styles.ribbonItem}>
            <Cpu className={`${styles.ribbonIcon} text-emerald-400`} />
            <span className={styles.ribbonText}>OpenAI</span>
          </div>

          <div className={styles.ribbonItem}>
            <CreditCard className={`${styles.ribbonIcon} text-sky-400`} />
            <span className={styles.ribbonText}>Razorpay</span>
          </div>

          <div className={styles.ribbonItem}>
            <Globe className={`${styles.ribbonIcon} text-blue-400`} />
            <span className={styles.ribbonText}>Google Workspace</span>
          </div>

          <div className={styles.ribbonItem}>
            <MessageSquare className={`${styles.ribbonIcon} text-purple-400`} />
            <span className={styles.ribbonText}>Slack</span>
          </div>

          <div className={styles.ribbonItem}>
            <Zap className={`${styles.ribbonIcon} text-amber-500`} />
            <span className={styles.ribbonText}>Zapier</span>
          </div>
        </div>

        {/* Central Orb */}
        <div className={styles.centerOrb}>
          <div className={styles.orbInnerLogo}>
            Grow<span>ixa</span>
          </div>
        </div>
      </div>

      {/* Search Input Mockup Card matching Image 5 */}
      <div className={styles.searchMockCard}>
        <div className={styles.searchInputText}>
          <Search className="w-5 h-5 text-purple-400" />
          <span>Search 10+ native integrations (Postmark, Razorpay, OpenAI, Claude)...</span>
        </div>
        <Link href="/login" className={styles.bookDemoBtn}>
          Book Demo <ArrowRight className="w-4 h-4 inline-block ml-1" />
        </Link>
      </div>
    </section>
  );
}
