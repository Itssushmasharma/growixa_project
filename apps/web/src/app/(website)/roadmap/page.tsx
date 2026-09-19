import React from "react";
import Link from "next/link";
import styles from "./roadmap.module.css";

export default function RoadmapPage() {
  return (
    <main className={styles.page}>
      <header className={styles.header}>
        <span className={styles.eyebrow}>Product Roadmap</span>
        <h1 className={styles.title}>Building the Future of Marketing</h1>
        <p className={styles.subtitle}>
          See what we&apos;re working on, what&apos;s coming next, and help us shape the future of Growixa.
        </p>
      </header>

      <div className={styles.kanbanBoard}>
        {/* NOW Column */}
        <div className={styles.kanbanCol}>
          <div className={styles.colHeader}>
            <span className={styles.colTitle}>Now</span>
            <span className={`${styles.colBadge} ${styles.badgeNow}`}>In Progress</span>
          </div>
          <div className={styles.ticketList}>
            <div className={styles.ticket}>
              <h3 className={styles.ticketTitle}>WhatsApp Business API V2</h3>
              <p className={styles.ticketDesc}>Full support for WhatsApp catalog integration and automated cart recovery messages.</p>
            </div>
            <div className={styles.ticket}>
              <h3 className={styles.ticketTitle}>AI Content Generator 2.0</h3>
              <p className={styles.ticketDesc}>Generate highly targeted email sequences and social posts based on CRM audience segments.</p>
            </div>
          </div>
        </div>

        {/* NEXT Column */}
        <div className={styles.kanbanCol}>
          <div className={styles.colHeader}>
            <span className={styles.colTitle}>Next</span>
            <span className={`${styles.colBadge} ${styles.badgeNext}`}>Up Next</span>
          </div>
          <div className={styles.ticketList}>
            <div className={styles.ticket}>
              <h3 className={styles.ticketTitle}>Custom Dashboard Widgets</h3>
              <p className={styles.ticketDesc}>Allow users to build their own reporting dashboards using a drag-and-drop widget library.</p>
            </div>
            <div className={styles.ticket}>
              <h3 className={styles.ticketTitle}>Shopify Deep Integration</h3>
              <p className={styles.ticketDesc}>Sync products, orders, and customers directly from Shopify into Growixa CRM in real-time.</p>
            </div>
            <div className={styles.ticket}>
              <h3 className={styles.ticketTitle}>Approval Workflows</h3>
              <p className={styles.ticketDesc}>Multi-step approval processes for agencies and enterprise teams before publishing content.</p>
            </div>
          </div>
        </div>

        {/* LATER Column */}
        <div className={styles.kanbanCol}>
          <div className={styles.colHeader}>
            <span className={styles.colTitle}>Later</span>
            <span className={`${styles.colBadge} ${styles.badgeLater}`}>Exploring</span>
          </div>
          <div className={styles.ticketList}>
            <div className={styles.ticket}>
              <h3 className={styles.ticketTitle}>TikTok & Shorts Publishing</h3>
              <p className={styles.ticketDesc}>Native video publishing and analytics for TikTok, YouTube Shorts, and Instagram Reels.</p>
            </div>
            <div className={styles.ticket}>
              <h3 className={styles.ticketTitle}>Predictive LTV Scoring</h3>
              <p className={styles.ticketDesc}>AI models to predict the lifetime value of a lead the moment they enter the CRM.</p>
            </div>
          </div>
        </div>
      </div>

      <div className={styles.submitIdea}>
        <h2>Have a feature request?</h2>
        <p>We build Growixa for you. If there&apos;s something you need that isn&apos;t on the roadmap, let us know.</p>
        <Link href="/contact" className={styles.submitBtn}>
          Submit an Idea
        </Link>
      </div>
    </main>
  );
}
