import React from 'react';
import Image from 'next/image';
import styles from './socialpilot-home.module.css';
import { SocialPilotFeaturesGrid } from './SocialPilotFeaturesGrid';

export function SocialPilotHome() {
  return (
    <div className={styles.container}>
      <header className={styles.sectionLight} style={{ padding: '1rem 2rem', display: 'flex', justifyContent: 'space-between', alignItems: 'center', borderBottom: '1px solid var(--color-border)' }}>
        <div style={{ fontWeight: 800, fontSize: '1.5rem', color: 'var(--color-text-main)' }}>Growixa</div>
        <nav style={{ display: 'flex', gap: '2rem', fontWeight: 600, color: 'var(--color-text-main)' }}>
          <div>Platform</div>
          <div>Solutions</div>
          <div>Resources</div>
          <div>Pricing</div>
        </nav>
        <div style={{ display: 'flex', gap: '1rem' }}>
          <button className={styles.btnSecondary} style={{ border: 'none', background: 'transparent' }}>Log In</button>
          <button className={styles.btnSecondary}>Request Demo</button>
          <button className={styles.btnPrimary}>Start Free Trial</button>
        </div>
      </header>

      <section className={styles.section} style={{ paddingTop: '6rem', paddingBottom: '4rem' }}>
        <div className={styles.textCenter}>
          <span className={styles.badge}>The Only Social Media Management Platform You Will Need to Drive Growth</span>
          <h1 className={styles.h1}>Everything you need to hit your social media goals</h1>
          <p className={styles.subtitle}>
            Growixa is a powerful social media management tool that helps you schedule posts, analyze performance, and engage with your audience, all from one place.
          </p>
          <div style={{ display: 'flex', gap: '1rem', justifyContent: 'center', marginTop: '2rem' }}>
            <button className={styles.btnPrimary}>Start Your Free Trial</button>
            <button className={styles.btnSecondary}>Talk to a Human</button>
          </div>
          <p style={{ marginTop: '1rem', fontSize: '0.875rem', color: 'var(--color-text-muted)' }}>No CC Required • Cancel Anytime</p>
        </div>

        {/* Dashboard Showcase */}
        <div className={styles.dashboardWrapper}>
          <div className={styles.dashboardGlow}></div>
          <Image 
            src="/growixa_dashboard.jpg" 
            alt="Growixa Dashboard showing analytics and calendar" 
            width={1200}
            height={675}
            className={styles.dashboardImage}
            priority
          />
        </div>
      </section>

      {/* Social Proof */}
      <section className={styles.sectionLight}>
        <div className={styles.section} style={{ paddingTop: '4rem', paddingBottom: '4rem' }}>
          <h3 style={{ textAlign: 'center', color: 'var(--color-text-muted)', fontSize: '1rem', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: '2rem' }}>
            Trusted by 13,000+ Agencies and Social Media Teams Worldwide
          </h3>
          <div style={{ display: 'flex', justifyContent: 'center', gap: '4rem', opacity: 0.5, flexWrap: 'wrap' }}>
            <div style={{ fontSize: '1.5rem', fontWeight: 800 }}>Adobe</div>
            <div style={{ fontSize: '1.5rem', fontWeight: 800 }}>Amazon</div>
            <div style={{ fontSize: '1.5rem', fontWeight: 800 }}>Netflix</div>
            <div style={{ fontSize: '1.5rem', fontWeight: 800 }}>Slack</div>
            <div style={{ fontSize: '1.5rem', fontWeight: 800 }}>Framer</div>
          </div>
        </div>
      </section>
      
      <SocialPilotFeaturesGrid />
      
    </div>
  );
}
