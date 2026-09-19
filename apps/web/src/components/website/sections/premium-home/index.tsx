import React from "react";
import Link from "next/link";
import { 
  Check, 
  X, 
  ArrowRight, 
  Zap, 
  Star, 
  Bot, 
  Sparkles, 
  Mic, 
  TrendingUp, 
  Layers, 
  Cpu 
} from "lucide-react";
import styles from "./premium-home.module.css";
import { DataFlowDiagram } from "../data-flow-diagram";
import { EcosystemSection } from "../ecosystem";
import { SecurityReliabilitySection } from "../security-reliability";
import { HowItWorksBentoSection } from "../how-it-works-bento";
import { PersonaGridSection } from "../persona-grid";
import { ChaoticWorkProblemSection } from "../chaotic-work-problem";
import { IntegrationHubOrbSection } from "../integration-hub-orb";
import { SocialDeepLinkArchSection } from "../social-deep-link-arch";

export function PremiumGrowixaHome() {
  return (
    <div className="w-full" style={{ background: "var(--paper, #0b0f19)" }}>
      {/* 1. HERO SECTION (Image 1 style AI Agent Platform) */}
      <section className={styles.hero}>
        <div className={styles.heroContent}>
          <span className={styles.eyebrow}>
            🏆 #1 AI Growth Platform of the Day
          </span>

          <h1 className={styles.heroTitle}>
            The Ultimate All-In-One <span>AI Growth Engine</span>
          </h1>

          <p className={styles.heroDesc}>
            Stop jumping between apps. Build, create, automate, and scale email campaigns, social dispatches, and brand analytics — all in one powerful AI hub.
          </p>

          <div className={styles.heroActions}>
            <Link href="/register" className={styles.primaryBtn}>
              Get Started Free <ArrowRight className="w-4 h-4 inline-block ml-1" />
            </Link>
            <Link href="/login" className={styles.secondaryBtn}>
              Explore Features <Sparkles className="w-4 h-4 inline-block ml-1 text-amber-400" />
            </Link>
          </div>

          {/* Rating Badge (Image 1 style) */}
          <div className={styles.ratingBadge}>
            <div className={styles.starsRow}>
              {[...Array(5)].map((_, idx) => (
                <Star key={idx} className="w-4 h-4 text-amber-400 fill-amber-400" />
              ))}
            </div>
            <span>Rated 4.9/5 by 12.5K+ Growth Teams & Founders</span>
          </div>
        </div>

        {/* Floating AI Cards Preview (Image 1 style) */}
        <div className={styles.heroImageContainer}>
          <div className={styles.floatingCardsGrid}>
            <div className={styles.floatCard}>
              <div className={styles.cardHeaderFlex}>
                <Mic className="w-5 h-5 text-purple-400" />
                <span className={styles.cardMockTitle}>Voice Assistant</span>
              </div>
              <div className={styles.cardMockDesc}>
                Natural language copy generation — just ask what campaign you need.
              </div>
            </div>

            <div className={styles.floatCard} style={{ marginTop: "20px" }}>
              <div className={styles.cardHeaderFlex}>
                <Bot className="w-5 h-5 text-amber-400" />
                <span className={styles.cardMockTitle}>AI Agents</span>
              </div>
              <div className={styles.cardMockDesc}>
                Gartner predicts 33%+ enterprise marketing tools will adopt AI agents by 2028.
              </div>
              <span className={styles.trendTag}>#1 trend in 2025</span>
            </div>

            <div className={styles.floatCard} style={{ marginTop: "40px" }}>
              <div className={styles.cardHeaderFlex}>
                <Cpu className="w-5 h-5 text-emerald-400" />
                <span className={styles.cardMockTitle}>Automation</span>
              </div>
              <div className={styles.cardMockDesc}>
                Streamline dispatches, Postmark webhooks, and Razorpay quotas automatically.
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* 2. BRANDS MARQUEE */}
      <section className={styles.brands}>
        <p className={styles.brandsText}>Trusted by modern growth teams and high-scale platforms</p>
        <div className={styles.marquee}>
          <div className={styles.marqueeTrack}>
            {[...Array(3)].map((_, i) => (
              <React.Fragment key={i}>
                <h3 className={styles.brandIcon} style={{ fontSize: '20px', fontWeight: '800' }}>combinator</h3>
                <h3 className={styles.brandIcon} style={{ fontSize: '20px', fontWeight: '800' }}>SEQUOIA</h3>
                <h3 className={styles.brandIcon} style={{ fontSize: '20px', fontWeight: '800' }}>Postmark</h3>
                <h3 className={styles.brandIcon} style={{ fontSize: '20px', fontWeight: '800' }}>OpenAI</h3>
                <h3 className={styles.brandIcon} style={{ fontSize: '20px', fontWeight: '800' }}>Razorpay</h3>
                <h3 className={styles.brandIcon} style={{ fontSize: '20px', fontWeight: '800' }}>Stripe</h3>
              </React.Fragment>
            ))}
          </div>
        </div>
      </section>

      {/* 3. CHAOTIC WORK PROBLEM SECTION (Image 4 concept) */}
      <ChaoticWorkProblemSection />

      {/* 4. GLOWING 3D INTEGRATION HUB ORB (Image 2 & 5 concepts) */}
      <IntegrationHubOrbSection />

      {/* 5. SOCIAL DEEP LINK ARCH (Image 3 concept) */}
      <SocialDeepLinkArchSection />

      {/* 6. COMPLETE AI PLATFORM TO POWER EVERYTHING (Image 1 concept) */}
      <section className={styles.roiSection}>
        <span className={styles.eyebrow} style={{ background: "rgba(245, 158, 11, 0.12)" }}>
          Overview
        </span>
        <h2 className={styles.roiTitle}>
          Complete AI Platform to <span>Power Everything</span>
        </h2>
        <p className={styles.roiSubtitle}>
          Growixa brings all your creative, analytical, and automation tools together into a seamless workspace designed to boost productivity.
        </p>

        <div className={styles.roiBento}>
          <div className={styles.calculatorCard}>
            <div style={{ display: "flex", alignItems: "center", gap: "10px", marginBottom: "16px" }}>
              <Mic className="w-6 h-6 text-purple-400" />
              <h3 style={{ fontSize: "1.25rem", fontWeight: "700", color: "#ffffff" }}>Voice & Conversational AI</h3>
            </div>
            <p style={{ color: "#94a3b8", fontSize: "0.95rem", lineHeight: "1.6" }}>
              Ask for email templates, Instagram copy, or contact list segments using natural language prompts.
            </p>
          </div>

          <div className={styles.calculatorCard}>
            <div style={{ display: "flex", alignItems: "center", gap: "10px", marginBottom: "16px" }}>
              <Bot className="w-6 h-6 text-amber-400" />
              <h3 style={{ fontSize: "1.25rem", fontWeight: "700", color: "#ffffff" }}>Brand Guardrail AI Agents</h3>
            </div>
            <p style={{ color: "#94a3b8", fontSize: "0.95rem", lineHeight: "1.6" }}>
              Enforce tone of voice, persona tags, and human marketing team sign-off before any campaign dispatches.
            </p>
          </div>

          <div className={styles.calculatorCard}>
            <div style={{ display: "flex", alignItems: "center", gap: "10px", marginBottom: "16px" }}>
              <TrendingUp className="w-6 h-6 text-emerald-400" />
              <h3 style={{ fontSize: "1.25rem", fontWeight: "700", color: "#ffffff" }}>Unified Growth Telemetry</h3>
            </div>
            <p style={{ color: "#94a3b8", fontSize: "0.95rem", lineHeight: "1.6" }}>
              Track real-time open/click delivery webhooks, Razorpay billing top-ups, and email quota usages.
            </p>
          </div>
        </div>
      </section>

      {/* 7. DATA FLOW DIAGRAM */}
      <DataFlowDiagram />

      {/* 8. HOW IT WORKS 3-STEP SETUP */}
      <HowItWorksBentoSection />

      {/* 9. ECOSYSTEM & SECURITY SECTIONS */}
      <EcosystemSection />
      <PersonaGridSection />
      <SecurityReliabilitySection />

      {/* 10. COMPARISON TABLE */}
      <section className={styles.comparisonSection}>
        <h2 className={styles.roiTitle}>Why choose <span>Growixa?</span></h2>
        <div className={styles.tableContainer}>
          <div className={`${styles.compRow} ${styles.compHeader}`}>
            <div className={`${styles.compCell} ${styles.compCellLeft}`}>Features</div>
            <div className={styles.compCell}>Others</div>
            <div className={`${styles.compCell} ${styles.compGrowixaHeader}`}>Growixa</div>
          </div>
          
          {[
            "Instant onboarding - no call required",
            "Unified Social, Email & SMS Inbox",
            "Human Marketing & AI Guardrails",
            "Automated Predictive Analytics",
            "Bank-Grade Security & SOC2 Ready"
          ].map((feature, idx) => (
            <div className={styles.compRow} key={idx}>
              <div className={`${styles.compCell} ${styles.compCellLeft}`}>{feature}</div>
              <div className={styles.compCell}><X color="var(--brand-gold, #f59e0b)" size={20} /></div>
              <div className={`${styles.compCell} ${styles.compGrowixa}`}><Check color="var(--paper, #0b0f19)" size={20} /></div>
            </div>
          ))}
        </div>
      </section>

      {/* 11. TESTIMONIALS */}
      <section className={styles.testimonials}>
        <h2 className={styles.roiTitle} style={{ textAlign: 'center' }}>Trusted by <span>Bold Brands</span></h2>
        <div className={styles.testiGrid}>
          <div className={styles.testiCard}>
            <p style={{ fontStyle: 'italic', color: 'var(--mut, #94a3b8)', marginBottom: '20px' }}>
              &quot;Great experience so far. We have a complex setup with Postmark, Razorpay, and OpenAI, and Growixa tied everything together seamlessly. Strongly recommend.&quot;
            </p>
            <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
              <div style={{ width: '40px', height: '40px', background: 'var(--paper-2, #1e293b)', borderRadius: '50%' }}></div>
              <div>
                <div style={{ fontWeight: '700', color: 'var(--ink, #f8fafc)' }}>Stephen G.</div>
                <div style={{ fontSize: '0.8rem', color: 'var(--mut, #94a3b8)' }}>CEO & Founder</div>
              </div>
            </div>
          </div>
          <div className={styles.testiCard}>
            <p style={{ fontStyle: 'italic', color: 'var(--mut, #94a3b8)', marginBottom: '20px' }}>
              &quot;Super efficient! Really enjoyed working with the Growixa platform. The bank-grade security and automated GDPR suppression list features give us total peace of mind.&quot;
            </p>
            <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
              <div style={{ width: '40px', height: '40px', background: 'var(--paper-2, #1e293b)', borderRadius: '50%' }}></div>
              <div>
                <div style={{ fontWeight: '700', color: 'var(--ink, #f8fafc)' }}>Arjun Sethi</div>
                <div style={{ fontSize: '0.8rem', color: 'var(--mut, #94a3b8)' }}>Co-Founder</div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* 12. DARK CTA BANNER & MASSIVE FOOTER */}
      <div className={styles.darkCtaContainer}>
        <div className={styles.darkCtaBox}>
          <h2 className={styles.darkCtaTitle}>
            Start Simplifying Your Growth Management Today!
          </h2>
          <p className={styles.darkCtaSubtitle}>
            Join thousands of modern startups and B2B platforms scaling with Growixa&apos;s unified AI growth engine.
          </p>
          <div style={{ display: "flex", gap: "16px", justifyContent: "center", flexWrap: "wrap" }}>
            <Link href="/register" className={styles.primaryBtn}>
              Get Started Free ↗
            </Link>
            <Link href="/login" className={styles.secondaryBtn}>
              Book a Demo
            </Link>
          </div>
        </div>
      </div>

      <footer className={styles.massiveFooter}>
        <div className={styles.footerContent}>
          <div>
            <h3 style={{ fontSize: '1.5rem', fontWeight: '800', marginBottom: '16px', color: 'var(--ink, #f8fafc)' }}>
              Save Time, Money, And <br/>Run A Better Platform.
            </h3>
            <p style={{ opacity: 0.8, maxWidth: '400px', marginBottom: '24px', color: 'var(--mut, #94a3b8)' }}>
              Growixa integrates with the tech stack you already use — Postmark, Razorpay, OpenAI, Claude, and Instagram.
            </p>
            <Link href="/register" className={styles.secondaryBtn} style={{ background: 'var(--brand-gold, #f59e0b)', color: '#000000', fontWeight: '700', border: 'none' }}>
              Get Started Free ↗
            </Link>
          </div>
          <div style={{ display: 'flex', gap: '60px', flexWrap: 'wrap' }}>
            <div>
              <h4 style={{ fontWeight: '700', marginBottom: '16px', opacity: 0.6 }}>PRODUCTS</h4>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '12px', opacity: 0.9 }}>
                <Link href="/login">Campaign Builder</Link>
                <Link href="/login">AI Brand Voice</Link>
                <Link href="/login">Social Scheduler</Link>
                <Link href="/login">Audit Logs</Link>
              </div>
            </div>
            <div>
              <h4 style={{ fontWeight: '700', marginBottom: '16px', opacity: 0.6 }}>RESOURCES</h4>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '12px', opacity: 0.9 }}>
                <Link href="#ecosystem">Integrations</Link>
                <Link href="#security">Security & SOC2</Link>
                <Link href="#how-it-works">How It Works</Link>
                <Link href="/docs">Help Center</Link>
              </div>
            </div>
          </div>
        </div>
        <div className={styles.footerGiantText}>GROWIXA</div>
      </footer>
    </div>
  );
}
