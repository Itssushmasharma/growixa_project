import React from "react";
import { MessageSquare, Zap, BarChart2, Check, ShieldCheck } from "lucide-react";
import styles from "./platform.module.css";

export default function PlatformPage() {
  return (
    <main className={styles.page}>
      <header className={styles.header}>
        <span className={styles.eyebrow}>Platform Overview</span>
        <h1 className={styles.title}>The Engine Powering Modern Marketing</h1>
        <p className={styles.subtitle}>
          Growixa combines your social media, email, SMS, and CRM into one unified, lightning-fast platform powered by cutting-edge AI.
        </p>
      </header>

      {/* Section 1: Unified Inbox */}
      <section className={styles.section}>
        <div className={styles.sectionContent}>
          <div className={styles.sectionIcon}>
            <MessageSquare size={32} />
          </div>
          <h2 className={styles.sectionTitle}>Unified Inbox</h2>
          <p className={styles.sectionDesc}>
            Stop switching tabs. Manage conversations from Instagram, Facebook, LinkedIn, Twitter, Email, and WhatsApp in a single feed.
          </p>
          <ul className={styles.featuresList}>
            <li className={styles.featureItem}><Check size={20} className={styles.checkIcon} /> Real-time WebSocket syncing</li>
            <li className={styles.featureItem}><Check size={20} className={styles.checkIcon} /> AI-powered Smart Replies</li>
            <li className={styles.featureItem}><Check size={20} className={styles.checkIcon} /> Team assignments & collision detection</li>
          </ul>
        </div>
        <div className={styles.sectionImage}>
          <div className={styles.placeholderGraph}>
            <div className={styles.bar} style={{width: '90%', background: 'var(--paper-2)', border: '1px solid var(--line)', height: '60px'}}></div>
            <div className={styles.bar} style={{width: '90%', background: 'var(--paper-2)', border: '1px solid var(--line)', height: '60px'}}></div>
            <div className={styles.bar} style={{width: '90%', background: 'var(--create)', height: '60px'}}></div>
          </div>
        </div>
      </section>

      {/* Section 2: Visual Automations */}
      <section className={`${styles.section} ${styles.sectionReverse}`}>
        <div className={styles.sectionContent}>
          <div className={styles.sectionIcon}>
            <Zap size={32} />
          </div>
          <h2 className={styles.sectionTitle}>Visual Automations</h2>
          <p className={styles.sectionDesc}>
            Build complex workflows without writing a single line of code. Drag and drop triggers, conditions, and actions to put your marketing on autopilot.
          </p>
          <ul className={styles.featuresList}>
            <li className={styles.featureItem}><Check size={20} className={styles.checkIcon} /> Drag-and-drop canvas</li>
            <li className={styles.featureItem}><Check size={20} className={styles.checkIcon} /> Pre-built templates for e-commerce</li>
            <li className={styles.featureItem}><Check size={20} className={styles.checkIcon} /> Multi-channel branching logic</li>
          </ul>
        </div>
        <div className={styles.sectionImage}>
          <div className={styles.placeholderGraph} style={{ alignItems: 'center', justifyContent: 'center' }}>
            <div style={{ width: '100px', height: '40px', background: 'var(--find)', borderRadius: '8px', color: 'var(--paper)', display: 'flex', alignItems: 'center', justifyContent: 'center', fontWeight: 'bold' }}>Trigger</div>
            <div style={{ width: '2px', height: '40px', background: 'var(--line)' }}></div>
            <div style={{ display: 'flex', gap: '20px' }}>
              <div style={{ width: '100px', height: '40px', background: 'var(--manage)', borderRadius: '8px', color: 'var(--paper)', display: 'flex', alignItems: 'center', justifyContent: 'center', fontWeight: 'bold' }}>Email</div>
              <div style={{ width: '100px', height: '40px', background: 'var(--create)', borderRadius: '8px', color: 'var(--paper)', display: 'flex', alignItems: 'center', justifyContent: 'center', fontWeight: 'bold' }}>SMS</div>
            </div>
          </div>
        </div>
      </section>

      {/* Section 3: Deep Analytics */}
      <section className={styles.section}>
        <div className={styles.sectionContent}>
          <div className={styles.sectionIcon}>
            <BarChart2 size={32} />
          </div>
          <h2 className={styles.sectionTitle}>Deep Analytics & AI Insights</h2>
          <p className={styles.sectionDesc}>
            Don&apos;t just look at charts. Growixa&apos;s AI engine analyzes your data and tells you exactly what content performs best and when to post it.
          </p>
          <ul className={styles.featuresList}>
            <li className={styles.featureItem}><Check size={20} className={styles.checkIcon} /> Custom KPI dashboards</li>
            <li className={styles.featureItem}><Check size={20} className={styles.checkIcon} /> Audience sentiment analysis</li>
            <li className={styles.featureItem}><Check size={20} className={styles.checkIcon} /> Competitor benchmarking</li>
          </ul>
        </div>
        <div className={styles.sectionImage}>
          <div className={styles.placeholderGraph}>
            <div className={styles.bar}></div>
            <div className={styles.bar}></div>
            <div className={styles.bar}></div>
            <div className={styles.bar}></div>
          </div>
        </div>
      </section>

      {/* Section 4: Enterprise Security */}
      <section className={`${styles.section} ${styles.sectionReverse}`}>
        <div className={styles.sectionContent}>
          <div className={styles.sectionIcon}>
            <ShieldCheck size={32} />
          </div>
          <h2 className={styles.sectionTitle}>Enterprise-Grade Security</h2>
          <p className={styles.sectionDesc}>
            Your data is your most valuable asset. We protect it with military-grade encryption, role-based access control, and SOC 2 Type II compliance.
          </p>
          <ul className={styles.featuresList}>
            <li className={styles.featureItem}><Check size={20} className={styles.checkIcon} /> SOC 2 Type II & GDPR Compliant</li>
            <li className={styles.featureItem}><Check size={20} className={styles.checkIcon} /> Role-Based Access Control (RBAC)</li>
            <li className={styles.featureItem}><Check size={20} className={styles.checkIcon} /> Single Sign-On (SAML/SSO)</li>
          </ul>
        </div>
        <div className={styles.sectionImage}>
          <div style={{ textAlign: 'center' }}>
            <ShieldCheck size={120} color="var(--create)" opacity={0.4} />
            <h3 style={{ fontSize: '1.5rem', fontWeight: 'bold', marginTop: '20px', color: 'var(--ink)' }}>100% Secure</h3>
          </div>
        </div>
      </section>

    </main>
  );
}
