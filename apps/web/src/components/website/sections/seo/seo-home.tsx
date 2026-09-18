"use client";

import React from 'react';
import styles from './seo-home.module.css';

export function SeoPlatformHome() {
  return (
    <div className={styles.container}>
      <div className={styles.bgGlow}></div>
      
      <header className={styles.header}>
        <div className={styles.logo}>Growixa SEO</div>
        <nav className={styles.nav}>
          <div className={styles.navItem}>Features</div>
          <div className={styles.navItem}>Rank Tracker</div>
          <div className={styles.navItem}>Audits</div>
          <div className={styles.navItem}>Pricing</div>
        </nav>
        <div>
          <button className={styles.btnPrimary} style={{ padding: '0.75rem 1.5rem', fontSize: '1rem' }}>
            Get Started
          </button>
        </div>
      </header>

      <main className={styles.hero}>
        <span className={styles.badge}>Next-Gen SEO Intelligence</span>
        <h1 className={styles.h1}>
          Dominate Search Rankings with <br />
          <span>AI-Powered SEO</span>
        </h1>
        <p className={styles.subtitle}>
          Stop guessing what Google wants. Growixa analyzes millions of data points to give you exact, actionable steps to outrank your competitors and drive massive organic traffic.
        </p>
        
        <button className={styles.btnPrimary}>Start Free SEO Audit</button>

        {/* Dynamic SEO Data Visualization replacing the static image */}
        <div className={styles.dataVizContainer}>
          <div className={styles.dataCard}>
            <div className={styles.dataLabel}>Organic Traffic</div>
            <div className={styles.dataValue}>
              245.8k <span className={styles.dataTrendUp}>↑ 34%</span>
            </div>
            <div style={{ height: '40px', marginTop: '1rem', background: 'linear-gradient(90deg, transparent 0%, rgba(16,185,129,0.2) 100%)', borderRadius: '4px' }}></div>
          </div>
          
          <div className={styles.dataCard}>
            <div className={styles.dataLabel}>Avg. Position</div>
            <div className={styles.dataValue}>
              3.2 <span className={styles.dataTrendUp}>↑ 1.5</span>
            </div>
            <div style={{ height: '40px', marginTop: '1rem', background: 'linear-gradient(90deg, transparent 0%, rgba(59,130,246,0.2) 100%)', borderRadius: '4px' }}></div>
          </div>
          
          <div className={styles.dataCard}>
            <div className={styles.dataLabel}>Domain Authority</div>
            <div className={styles.dataValue}>
              78 <span className={styles.dataTrendUp}>↑ 2</span>
            </div>
            <div style={{ height: '40px', marginTop: '1rem', background: 'linear-gradient(90deg, transparent 0%, rgba(16,185,129,0.2) 100%)', borderRadius: '4px' }}></div>
          </div>
        </div>
      </main>

      <section className={styles.featuresSection}>
        <div style={{ textAlign: 'center' }}>
          <h2 className={styles.h1} style={{ fontSize: '3rem' }}>Everything you need to scale organic growth</h2>
        </div>
        
        <div className={styles.featuresGrid}>
          <div className={styles.featureCard}>
            <div className={styles.featureIcon}>📈</div>
            <h3 className={styles.featureTitle}>Real-time Rank Tracking</h3>
            <p className={styles.featureDesc}>Track your target keywords across global search engines with daily updates and competitor movement alerts.</p>
          </div>
          
          <div className={styles.featureCard}>
            <div className={styles.featureIcon}>🔍</div>
            <h3 className={styles.featureTitle}>Deep Technical Audits</h3>
            <p className={styles.featureDesc}>Crawl your entire website to instantly find and fix broken links, missing tags, and core web vital issues.</p>
          </div>
          
          <div className={styles.featureCard}>
            <div className={styles.featureIcon}>🤖</div>
            <h3 className={styles.featureTitle}>AI Content Optimizer</h3>
            <p className={styles.featureDesc}>Write content that ranks. Our AI analyzes top-ranking pages to give you precise keyword and LSI recommendations.</p>
          </div>
        </div>
      </section>
    </div>
  );
}
