import React from "react";
import Link from "next/link";
import { Check, X } from "lucide-react";
import styles from "./premium-home.module.css";
import { DataFlowDiagram } from "../data-flow-diagram";

export function PremiumGrowixaHome() {
  return (
    <div className="w-full" style={{ background: "#ffffff" }}>
      {/* 1. HERO SECTION */}
      <section className={styles.hero}>
        <div className={styles.heroContent}>
          <span className={styles.eyebrow}>Trust the numbers</span>
          <h1 className={styles.heroTitle}>
            Claim the Marketing ROI Your Startup Deserves
          </h1>
          <p className={styles.heroDesc}>
            Easily organize, optimize, and automate marketing campaigns — helping startups recover thousands of hours they didn&apos;t know they were losing.
          </p>
          <div className={styles.heroActions}>
            <Link href="/register" className={styles.primaryBtn}>
              Get Started ↗
            </Link>
            <Link href="/login" className={styles.secondaryBtn}>
              Book a demo
            </Link>
          </div>
        </div>

        {/* Floating Cards Graphic */}
        <div className={styles.heroImageContainer}>
          <div className={styles.floatingCardsGrid}>
            <div className={styles.floatCard}>
              <div className={styles.cardMockTitle}>Audience Growth</div>
              <div className={styles.cardMockValue}>+240%</div>
              <div className={styles.cardMockGraph}>
                <div className={styles.graphBar} style={{ height: "40%" }} />
                <div className={styles.graphBar} style={{ height: "60%" }} />
                <div className={styles.graphBar} style={{ height: "50%" }} />
                <div className={styles.graphBar} style={{ height: "80%", background: "#2a41ff" }} />
              </div>
            </div>
            
            <div className={styles.floatCard} style={{ marginTop: "40px" }}>
              <div className={styles.cardMockTitle}>Campaign ROI</div>
              <div className={styles.cardMockValue}>$12,450</div>
              <div className={styles.cardMockGraph}>
                <div className={styles.graphBar} style={{ height: "30%" }} />
                <div className={styles.graphBar} style={{ height: "50%" }} />
                <div className={styles.graphBar} style={{ height: "70%" }} />
                <div className={styles.graphBar} style={{ height: "100%", background: "#2a41ff" }} />
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* 2. BRANDS MARQUEE */}
      <section className={styles.brands}>
        <p className={styles.brandsText}>Trusted by famous companies worldwide</p>
        <div className={styles.marquee}>
          <div className={styles.marqueeTrack}>
            {[...Array(3)].map((_, i) => (
              <React.Fragment key={i}>
                <h3 className={styles.brandIcon} style={{ fontSize: '20px', fontWeight: '800' }}>combinator</h3>
                <h3 className={styles.brandIcon} style={{ fontSize: '20px', fontWeight: '800' }}>SEQUOIA</h3>
                <h3 className={styles.brandIcon} style={{ fontSize: '20px', fontWeight: '800' }}>PostHog</h3>
                <h3 className={styles.brandIcon} style={{ fontSize: '20px', fontWeight: '800' }}>type</h3>
                <h3 className={styles.brandIcon} style={{ fontSize: '20px', fontWeight: '800' }}>KARAT</h3>
                <h3 className={styles.brandIcon} style={{ fontSize: '20px', fontWeight: '800' }}>EXPLO</h3>
              </React.Fragment>
            ))}
          </div>
        </div>
      </section>

      {/* 3. CALCULATOR SECTION */}
      <section className={styles.roiSection}>
        <h2 className={styles.roiTitle}>
          See How Much Time & Cash You Could <span>Save</span>
        </h2>
        <p className={styles.roiSubtitle}>
          Easily qualify, optimize, and launch campaigns — helping startups scale faster.
        </p>

        <div className={styles.roiBento}>
          <div className={styles.calculatorCard}>
            <label className={styles.calcLabel}>Team Size</label>
            <select className={styles.calcSelect} defaultValue="8">
              <option value="1">1-5</option>
              <option value="8">5-15</option>
              <option value="20">15-50</option>
            </select>

            <label className={styles.calcLabel}>Monthly Marketing Spend</label>
            <select className={styles.calcSelect} defaultValue="75000">
              <option value="10000">$10,000</option>
              <option value="50000">$50,000</option>
              <option value="75000">$75,000</option>
            </select>
          </div>

          <div className={styles.resultCard}>
            <div className={styles.resultTitle}>Estimate your Marketing ROI</div>
            <p style={{ color: '#5c6488', fontSize: '0.9rem' }}>Startups can save up to 40 hours a week.</p>
            <div className={styles.resultValue}>$1,250 - $4,500</div>
            <Link href="/register" className={styles.primaryBtn} style={{ width: '100%', marginTop: '10px' }}>
              Get Started ↗
            </Link>
          </div>
        </div>
      </section>

      {/* 4. DATA FLOW DIAGRAM (User approved feature) */}
      <DataFlowDiagram />

      {/* 5. COMPARISON TABLE */}
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
            "Human Marketing Experts Available",
            "Automated Predictive Analytics",
            "Unlimited Team Seats"
          ].map((feature, idx) => (
            <div className={styles.compRow} key={idx}>
              <div className={`${styles.compCell} ${styles.compCellLeft}`}>{feature}</div>
              <div className={styles.compCell}><X color="#ff3f73" size={20} /></div>
              <div className={`${styles.compCell} ${styles.compGrowixa}`}><Check color="#ffffff" size={20} /></div>
            </div>
          ))}
        </div>
      </section>

      {/* 6. TESTIMONIALS */}
      <section className={styles.testimonials}>
        <h2 className={styles.roiTitle} style={{ textAlign: 'center' }}>Trusted by <span>Bold Brands</span></h2>
        <div className={styles.testiGrid}>
          <div className={styles.testiCard}>
            <p style={{ fontStyle: 'italic', color: '#5c6488', marginBottom: '20px' }}>
              &quot;Great experience so far. We have a complex setup and they have way outperformed the previous two solutions we had tried out. Strongly recommend.&quot;
            </p>
            <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
              <div style={{ width: '40px', height: '40px', background: '#e1e5ff', borderRadius: '50%' }}></div>
              <div>
                <div style={{ fontWeight: '700', color: '#0b102b' }}>Stephen.G</div>
                <div style={{ fontSize: '0.8rem', color: '#8f98b6' }}>CEO & Founder</div>
              </div>
            </div>
          </div>
          <div className={styles.testiCard}>
            <p style={{ fontStyle: 'italic', color: '#5c6488', marginBottom: '20px' }}>
              &quot;Super efficient! Really enjoyed working with the Growixa team! Highly recommend for startups looking to scale.&quot;
            </p>
            <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
              <div style={{ width: '40px', height: '40px', background: '#e1e5ff', borderRadius: '50%' }}></div>
              <div>
                <div style={{ fontWeight: '700', color: '#0b102b' }}>Arjun Sethi</div>
                <div style={{ fontSize: '0.8rem', color: '#8f98b6' }}>Co-Founder</div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* 7. MASSIVE FOOTER */}
      <footer className={styles.massiveFooter}>
        <div className={styles.footerContent}>
          <div>
            <h3 style={{ fontSize: '1.5rem', fontWeight: '800', marginBottom: '16px' }}>Save Time, Money, And <br/>Run A Better Startup.</h3>
            <p style={{ opacity: 0.8, maxWidth: '400px', marginBottom: '24px' }}>Growixa integrates with the platforms you already use, making it easy to bring everything together in one place.</p>
            <Link href="/register" className={styles.secondaryBtn} style={{ background: '#ffffff', color: '#2a41ff' }}>
              Get Started ↗
            </Link>
          </div>
          <div style={{ display: 'flex', gap: '60px' }}>
            <div>
              <h4 style={{ fontWeight: '700', marginBottom: '16px', opacity: 0.6 }}>PRODUCTS</h4>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '12px', opacity: 0.9 }}>
                <Link href="#">Inbox</Link>
                <Link href="#">Automations</Link>
                <Link href="#">Analytics</Link>
              </div>
            </div>
            <div>
              <h4 style={{ fontWeight: '700', marginBottom: '16px', opacity: 0.6 }}>RESOURCES</h4>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '12px', opacity: 0.9 }}>
                <Link href="#">Help Center</Link>
                <Link href="#">Book a Demo</Link>
                <Link href="#">Blog</Link>
              </div>
            </div>
          </div>
        </div>
        <div className={styles.footerGiantText}>GROWIXA</div>
      </footer>
    </div>
  );
}
