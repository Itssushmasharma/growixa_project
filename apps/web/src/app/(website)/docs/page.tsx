import React from "react";
import Link from "next/link";
import { Search, Code2, BookOpen, Key, Webhook } from "lucide-react";
import styles from "./docs.module.css";

export default function DocsPage() {
  return (
    <main className={styles.page}>
      {/* Sidebar Navigation */}
      <aside className={styles.sidebar}>
        <Link href="/" className={styles.logo}>Grow<span>ixa</span></Link>
        
        <div className={styles.navGroup}>
          <div className={styles.navTitle}>Getting Started</div>
          <Link href="/docs" className={styles.navLinkActive}>Introduction</Link>
          <Link href="/docs/quickstart" className={styles.navLink}>Quick Start Guide</Link>
          <Link href="/docs/authentication" className={styles.navLink}>Authentication</Link>
        </div>

        <div className={styles.navGroup}>
          <div className={styles.navTitle}>Core Concepts</div>
          <Link href="/docs/inbox" className={styles.navLink}>Unified Inbox</Link>
          <Link href="/docs/automations" className={styles.navLink}>Visual Automations</Link>
          <Link href="/docs/crm" className={styles.navLink}>Audience CRM</Link>
        </div>

        <div className={styles.navGroup}>
          <div className={styles.navTitle}>API Reference</div>
          <Link href="/docs/api/rest" className={styles.navLink}>REST API Overview</Link>
          <Link href="/docs/api/webhooks" className={styles.navLink}>Webhooks</Link>
          <Link href="/docs/api/rate-limits" className={styles.navLink}>Rate Limits</Link>
        </div>
      </aside>

      {/* Main Content Area */}
      <section className={styles.content}>
        <header className={styles.header}>
          <span className={styles.eyebrow}>Developer & Help Center</span>
          <h1 className={styles.title}>Growixa Documentation</h1>
          <p className={styles.subtitle}>
            Learn how to integrate Growixa into your tech stack, build custom automations, and manage your marketing data programmatically.
          </p>
        </header>

        <div className={styles.searchBar}>
          <Search size={20} className={styles.searchIcon} />
          <input type="text" placeholder="Search documentation, API endpoints, or tutorials..." className={styles.searchInput} />
        </div>

        <div className={styles.cardGrid}>
          {/* Quick Start Card */}
          <Link href="/docs/quickstart" className={styles.card}>
            <h2 className={styles.cardTitle}><BookOpen size={24} color="#2a41ff" /> Quick Start Guide</h2>
            <p className={styles.cardDesc}>Connect your first social account and set up your unified inbox in under 5 minutes.</p>
          </Link>

          {/* API Reference Card */}
          <Link href="/docs/api/rest" className={styles.card}>
            <h2 className={styles.cardTitle}><Code2 size={24} color="#2a41ff" /> API Reference</h2>
            <p className={styles.cardDesc}>Explore our REST API to programmatically manage contacts, posts, and analytics data.</p>
          </Link>

          {/* Authentication Card */}
          <Link href="/docs/authentication" className={styles.card}>
            <h2 className={styles.cardTitle}><Key size={24} color="#2a41ff" /> Authentication</h2>
            <p className={styles.cardDesc}>Learn how to generate API keys and use OAuth 2.0 to authenticate your requests securely.</p>
          </Link>

          {/* Webhooks Card */}
          <Link href="/docs/api/webhooks" className={styles.card}>
            <h2 className={styles.cardTitle}><Webhook size={24} color="#2a41ff" /> Webhooks</h2>
            <p className={styles.cardDesc}>Subscribe to real-time events like incoming messages, new contacts, or campaign completions.</p>
          </Link>
        </div>
      </section>
    </main>
  );
}
