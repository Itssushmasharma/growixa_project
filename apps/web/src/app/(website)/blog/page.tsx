"use client";

import { useState } from "react";
import { PageHero, Sec, Head, ClosingCta } from "@/components/website/sections/page-kit";
import styles from "./blog.module.css";

interface Article {
  id: string;
  category: "Deliverability" | "AI & Content" | "Growth" | "Architecture";
  title: string;
  excerpt: string;
  author: string;
  role: string;
  date: string;
  readTime: string;
  content: string[];
}

const ARTICLES: Article[] = [
  {
    id: "deliverability-at-scale",
    category: "Deliverability",
    title: "Email Deliverability at Scale: SPF, DKIM, DMARC, and Automated Warm-up Math",
    excerpt:
      "A deep technical breakdown of mailbox provider reputation algorithms, DNS authentication, bounce suppression thresholds, and why inbox placement always beats vanity dispatch volume.",
    author: "Growixa Infra Team",
    role: "DevOps & MTA Architecture",
    date: "September 8, 2026",
    readTime: "8 min read",
    content: [
      "Modern mailbox providers (Google Workspace, Microsoft 365, Yahoo) no longer evaluate email senders solely by IP address. Instead, domain reputation, cryptographic authentication (DKIM alignment, strict SPF records, and DMARC enforcement), and recipient engagement signals dictate whether an email reaches the Primary inbox or the Spam folder.",
      "In Growixa, every sender identity undergoes a rigorous 30-day automated warm-up ramp. By gradually scaling daily dispatch volumes and enforcing strict bounce suppression thresholds (suspending campaigns if hard bounces exceed 1.8%), our infrastructure protects domain reputation before deliverability degradation can occur.",
      "Furthermore, our multi-tenant queue architecture enforces account isolation at the MTA layer. Even under high-throughput marketing blasts, each workspace's sending reputation remains completely isolated and protected against neighborhood abuse.",
    ],
  },
  {
    id: "human-in-the-loop-ai",
    category: "AI & Content",
    title: "Why Human-in-the-Loop AI Converts 2.4x Better Than Autonomous Blasts",
    excerpt:
      "Uncontrolled autonomous email generation burns sender domains and alienates leads. Discover how brand-voice guardrails and deterministic human review gates double reply rates.",
    author: "Product Team",
    role: "AI Studio & Growth",
    date: "September 4, 2026",
    readTime: "6 min read",
    content: [
      "The promise of fully autonomous AI marketing tools often results in generic, repetitive, or hallucinated claims sent to hundreds of valuable prospects. In B2B sales and high-ticket conversion, an off-brand message doesn't just fail to convert—it burns brand credibility and triggers spam reports.",
      "Growixa implements a strict architectural principle: AI generates intelligent drafts, subject line variants, and persona-adapted body copy, but a human must review and approve every consequential communication before dispatch.",
      "Our early cohort data across 50 design partner workspaces showed that human-reviewed AI campaigns achieved a 2.4x higher positive reply rate and reduced unsubscribe rates by 68% compared to unmoderated AI generation.",
    ],
  },
  {
    id: "behavioral-lead-intelligence",
    category: "Growth",
    title: "Behavioral Lead Intelligence: Moving from Cold Contact Lists to Active Pipeline",
    excerpt:
      "Static CSV lists decay at 2.1% per month. Learn how dynamic behavior-based segmentation and intent signal scoring transform passive contacts into high-velocity pipeline.",
    author: "Growth Strategy",
    role: "Quantitative Marketing",
    date: "August 30, 2026",
    readTime: "7 min read",
    content: [
      "Traditional marketing automation treats every contact in a list identically: they receive the same scheduled email at the same interval. In reality, prospect intent fluctuates dynamically based on website page visits, documentation reads, and previous campaign clicks.",
      "With Growixa's behavioral segmentation engine, contacts dynamically enter and exit sequences based on deterministic rules. If a lead visits your pricing page or reads your security posture, the system flags a high-intent signal and surfaces an actionable next step in the Growth Command Center.",
      "By replacing static blasting with event-driven follow-ups, growth teams capture buyers during their active decision window rather than weeks after interest has cooled.",
    ],
  },
  {
    id: "multi-user-isolation",
    category: "Architecture",
    title: "Single-Tenant Multi-User Architecture: Why Account Isolation is Non-Negotiable",
    excerpt:
      "How database-layer account scoping, Fernet symmetric encryption, and strict RBAC protect company assets, customer contacts, and API credentials from data leaks.",
    author: "Core Security",
    role: "Security & Infrastructure",
    date: "August 24, 2026",
    readTime: "9 min read",
    content: [
      "SaaS data security cannot rely on developer discipline or application-level filtering alone. A single missing 'WHERE account_id = ...' clause in an API repository can expose confidential contacts or marketing plans to unauthorized users.",
      "Growixa enforces tenant isolation directly at the database query layer. Every database model explicitly scopes data by account ID, and all sensitive third-party credentials (SMTP passwords, AI keys) are encrypted at rest using AES-128 Fernet cryptography with keys rotated via secure environment stores.",
      "Our centralized RBAC dependencies audit every incoming HTTP request against role permissions (Owner, Admin, Member, View-Only), ensuring that view-only analysts cannot trigger sends and audit trails record every consequential action.",
    ],
  },
];

const CATEGORIES = ["All", "Deliverability", "AI & Content", "Growth", "Architecture"] as const;

export default function BlogPage() {
  const [selectedCategory, setSelectedCategory] = useState<string>("All");
  const [expandedArticleId, setExpandedArticleId] = useState<string | null>(null);

  const filteredArticles =
    selectedCategory === "All"
      ? ARTICLES
      : ARTICLES.filter((a) => a.category === selectedCategory);

  const toggleExpand = (id: string) => {
    setExpandedArticleId((prev) => (prev === id ? null : id));
  };

  return (
    <>
      <PageHero
        hue="create"
        title="Engineering Transparency & Growth Telemetry Insights"
        lede="In-depth technical writeups, deliverability playbooks, and architectural lessons from building the Growixa autonomous growth platform."
      />

      <Sec hue="create">
        <Head
          center
          title="Featured Engineering & Growth Publications"
          lede="Tested frameworks, real deliverability numbers, and architectural patterns from our core team."
        />

        <div className={styles.filterBar} role="group" aria-label="Article Categories">
          {CATEGORIES.map((cat) => (
            <button
              key={cat}
              type="button"
              onClick={() => setSelectedCategory(cat)}
              className={`${styles.filterChip} ${selectedCategory === cat ? styles.filterChipActive : ""}`}
            >
              {cat}
            </button>
          ))}
        </div>

        <div className={styles.blogGrid}>
          {filteredArticles.map((article) => {
            const isExpanded = expandedArticleId === article.id;

            return (
              <article key={article.id} className={styles.articleCard}>
                <div className={styles.cardHeader}>
                  <span className={styles.categoryTag}>{article.category}</span>
                  <span className={styles.readTime}>{article.readTime}</span>
                </div>

                <h3 className={styles.articleTitle}>{article.title}</h3>
                <p className={styles.articleExcerpt}>{article.excerpt}</p>

                {isExpanded && (
                  <div className={styles.articleFullContent}>
                    {article.content.map((paragraph, idx) => (
                      <p key={idx}>{paragraph}</p>
                    ))}
                  </div>
                )}

                <div className={styles.cardFooter}>
                  <div className={styles.authorMeta}>
                    <div className={styles.authorAvatar}>
                      {article.author.charAt(0)}
                    </div>
                    <div className={styles.authorDetails}>
                      <span className={styles.authorName}>{article.author}</span>
                      <span className={styles.publishDate}>{article.date}</span>
                    </div>
                  </div>

                  <button
                    type="button"
                    onClick={() => toggleExpand(article.id)}
                    className={styles.readMoreBtn}
                    aria-expanded={isExpanded}
                  >
                    {isExpanded ? "Collapse article ↑" : "Read full article →"}
                  </button>
                </div>
              </article>
            );
          })}
        </div>
      </Sec>

      <ClosingCta
        title="Ready to turn growth goals into approved campaigns?"
        body="Join high-velocity teams using Growixa to automate audience intelligence, email deliverability, and marketing workflows."
        primary={{ to: "/register", label: "Start free forever" }}
        secondary={{ to: "/pricing", label: "Compare plans" }}
      />
    </>
  );
}
