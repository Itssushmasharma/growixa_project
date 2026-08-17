import React from "react";
import Link from "next/link";
import { notFound } from "next/navigation";
import { getArticleBySlug, getAllArticles, DOC_CATEGORIES } from "@/lib/docs/data";
import { DocsSidebar } from "@/components/docs/docs-sidebar";
import { DocsToc } from "@/components/docs/docs-toc";
import { DocsCallout } from "@/components/docs/docs-callout";
import styles from "./article.module.css";

interface ArticlePageProps {
  params: Promise<{
    category: string;
    slug: string;
  }>;
}

export async function generateMetadata({ params }: ArticlePageProps) {
  const { category, slug } = await params;
  const match = getArticleBySlug(category, slug);
  if (!match) return { title: "Documentation | Growixa" };

  return {
    title: `${match.article.title} | Growixa Docs`,
    description: match.article.excerpt,
  };
}

export default async function DocArticlePage({ params }: ArticlePageProps) {
  const { category, slug } = await params;
  const match = getArticleBySlug(category, slug);

  if (!match) {
    notFound();
  }

  const { article, category: cat } = match;
  const allArticles = getAllArticles();
  const currentIndex = allArticles.findIndex(
    (a) => a.slug === article.slug && a.category === cat.id,
  );
  const prevArticle = currentIndex > 0 ? allArticles[currentIndex - 1] : null;
  const nextArticle = currentIndex < allArticles.length - 1 ? allArticles[currentIndex + 1] : null;

  return (
    <div className={styles.pageLayout}>
      {/* Left Navigation Sidebar */}
      <DocsSidebar currentCategory={cat.id} currentSlug={article.slug} />

      {/* Main Reading Column */}
      <main className={styles.mainContent}>
        {/* Breadcrumb Navigation */}
        <nav className={styles.breadcrumbs} aria-label="Breadcrumbs">
          <Link href="/docs" className={styles.crumbLink}>
            Docs
          </Link>
          <span className={styles.crumbSeparator}>/</span>
          <Link href={`/docs#${cat.id}`} className={styles.crumbLink}>
            {cat.name}
          </Link>
          <span className={styles.crumbSeparator}>/</span>
          <span className={styles.crumbActive}>{article.title}</span>
        </nav>

        {/* Article Header */}
        <header className={styles.articleHeader}>
          <div className={styles.metaRow}>
            <span className={styles.categoryBadge}>
              {cat.icon} {cat.name}
            </span>
            <span className={styles.readTime}>⏱️ {article.readingTimeMinutes} min read</span>
            <span className={styles.updateTime}>Updated {article.lastUpdated}</span>
          </div>

          <h1 className={styles.articleTitle}>
            {article.icon && <span className={styles.headerIcon}>{article.icon}</span>}
            {article.title}
          </h1>

          <p className={styles.articleExcerpt}>{article.excerpt}</p>
        </header>

        {/* Dynamic Helpful Callout Box */}
        {cat.id === "getting-started" && (
          <DocsCallout type="tip" title="Quick Setup Tip">
            Follow the steps below in order to ensure high email deliverability and avoid spam
            filters when launching your first campaign.
          </DocsCallout>
        )}
        {cat.id === "contacts" && slug === "restoring-deleted-contacts" && (
          <DocsCallout type="important" title="Quota Limit Protection">
            Restoring active contacts checks your subscription quota (`max_contacts`). Upgrading
            your plan allows unlimited audience expansion without data loss.
          </DocsCallout>
        )}

        {/* Article Sections */}
        <div className={styles.sectionsContainer}>
          {article.sections.map((section) => (
            <section key={section.id} id={section.id} className={styles.docSection}>
              <h2 className={styles.sectionHeading}>{section.title}</h2>
              <div className={styles.sectionBody}>
                {section.content.split("\n\n").map((paragraph, pIdx) => {
                  if (
                    paragraph.startsWith("- ") ||
                    paragraph.startsWith("1. ") ||
                    paragraph.startsWith("2. ") ||
                    paragraph.startsWith("3. ")
                  ) {
                    const lines = paragraph.split("\n");
                    const isOrdered = paragraph.startsWith("1. ");
                    const ListTag = isOrdered ? "ol" : "ul";

                    return (
                      <ListTag key={pIdx} className={styles.listBlock}>
                        {lines.map((line, lIdx) => {
                          const cleanLine = line.replace(/^[-*]\s+|\d+\.\s+/, "");
                          return <li key={lIdx}>{cleanLine}</li>;
                        })}
                      </ListTag>
                    );
                  }

                  return <p key={pIdx}>{paragraph}</p>;
                })}
              </div>
            </section>
          ))}
        </div>

        {/* Article Tags */}
        {article.tags.length > 0 && (
          <div className={styles.tagsRow}>
            <span className={styles.tagsLabel}>Tags:</span>
            {article.tags.map((tag) => (
              <span key={tag} className={styles.tagBadge}>
                #{tag}
              </span>
            ))}
          </div>
        )}

        {/* Pagination: Prev / Next Article */}
        <nav className={styles.paginationNav} aria-label="Previous and Next Articles">
          {prevArticle ? (
            <Link
              href={`/docs/${prevArticle.category}/${prevArticle.slug}`}
              className={styles.prevLink}
            >
              <span className={styles.navDirection}>← Previous</span>
              <span className={styles.navTitle}>{prevArticle.title}</span>
            </Link>
          ) : (
            <div />
          )}

          {nextArticle && (
            <Link
              href={`/docs/${nextArticle.category}/${nextArticle.slug}`}
              className={styles.nextLink}
            >
              <span className={styles.navDirection}>Next →</span>
              <span className={styles.navTitle}>{nextArticle.title}</span>
            </Link>
          )}
        </nav>
      </main>

      {/* Right Sticky Table of Contents */}
      <DocsToc sections={article.sections} />
    </div>
  );
}
