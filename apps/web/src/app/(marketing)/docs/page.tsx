import React from "react";
import Link from "next/link";
import { DOC_CATEGORIES, getAllArticles } from "@/lib/docs/data";
import { DocsSearch } from "@/components/docs/docs-search";
import styles from "./docs.module.css";

export const metadata = {
  title: "Documentation & Help Center | Growixa",
  description:
    "Comprehensive guides, integration walkthroughs, and tutorials for the Growixa growth and email marketing platform.",
};

export default function DocsLandingPage() {
  const allArticles = getAllArticles();
  const totalArticles = allArticles.length;

  return (
    <div className={styles.docsContainer}>
      {/* Hero Header */}
      <section className={styles.heroSection}>
        <div className={styles.heroBadge}>📖 Knowledge Base & User Guides</div>
        <h1 className={styles.heroTitle}>How can we help you grow?</h1>
        <p className={styles.heroSubtitle}>
          Explore {totalArticles} detailed guides, integration playbooks, and best practices to
          master Growixa email campaigns, dynamic segments, and AI automation.
        </p>

        {/* Global Live Search */}
        <div className={styles.heroSearchWrapper}>
          <DocsSearch
            placeholder="Search guides, SMTP, SPF, Segments, Soft Delete, AI Studio..."
            autoFocus
          />
        </div>

        {/* Quick Suggestion Chips */}
        <div className={styles.quickChips}>
          <span className={styles.quickLabel}>Popular topics:</span>
          <Link href="/docs/getting-started/quickstart" className={styles.chip}>
            ⚡ 5-Min Quickstart
          </Link>
          <Link href="/docs/contacts/importing-contacts" className={styles.chip}>
            📥 CSV Imports
          </Link>
          <Link href="/docs/getting-started/domain-verification" className={styles.chip}>
            🛡️ SPF & DKIM
          </Link>
          <Link href="/docs/integrations/postmark-setup" className={styles.chip}>
            📨 Postmark Delivery
          </Link>
          <Link href="/docs/contacts/restoring-deleted-contacts" className={styles.chip}>
            🔄 Restore Contacts
          </Link>
        </div>
      </section>

      {/* Category Cards Grid */}
      <section className={styles.categoriesSection} aria-label="Documentation Categories">
        <div className={styles.sectionHeader}>
          <h2 className={styles.sectionTitle}>Browse by Topic</h2>
          <p className={styles.sectionSubtitle}>
            Find step-by-step documentation for every feature area in Growixa.
          </p>
        </div>

        <div className={styles.categoriesGrid}>
          {DOC_CATEGORIES.map((category) => (
            <div key={category.id} className={styles.categoryCard}>
              <div className={styles.categoryHeader}>
                <div className={styles.categoryIconWrap}>{category.icon}</div>
                <div>
                  <h3 className={styles.categoryName}>{category.name}</h3>
                  <span className={styles.articleCount}>
                    {category.articles.length} article{category.articles.length > 1 ? "s" : ""}
                  </span>
                </div>
              </div>

              <p className={styles.categoryDesc}>{category.description}</p>

              <ul className={styles.categoryArticleLinks}>
                {category.articles.map((article) => (
                  <li key={article.slug}>
                    <Link href={`/docs/${category.id}/${article.slug}`} className={styles.catLink}>
                      <span className={styles.linkIcon}>{article.icon || "📄"}</span>
                      <span className={styles.linkTitle}>{article.title}</span>
                    </Link>
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </div>
      </section>

      {/* Featured Help Spotlight */}
      <section className={styles.spotlightSection}>
        <div className={styles.spotlightCard}>
          <div className={styles.spotlightIcon}>✨</div>
          <div className={styles.spotlightContent}>
            <h3 className={styles.spotlightTitle}>Need Contextual Help in the Dashboard?</h3>
            <p className={styles.spotlightText}>
              You don&apos;t have to leave your active campaign or audience list. Look for the{" "}
              <strong>(?)</strong> icons next to form fields, or click{" "}
              <strong>&ldquo;Help &amp; Docs&rdquo;</strong> in the dashboard sidebar to open our
              instant slide-over assistant.
            </p>
          </div>
          <Link href="/dashboard" className={styles.spotlightAction}>
            Go to Dashboard →
          </Link>
        </div>
      </section>
    </div>
  );
}
